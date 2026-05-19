# -*- coding: utf-8 -*-
"""
services/favorite_place_service.py
----------------------------------
장소 즐겨찾기 도메인 서비스 레이어.

주요 함수:
    - toggle_favorite_place() : 즐겨찾기 토글 (없으면 INSERT, 있으면 DELETE)
    - list_favorite_places()  : 사용자별 즐겨찾기 목록 (favorited_at DESC)

[설계 결정]
- 외부 API 입력은 `places.content_id` (한국관광공사 ID, 카드가 보유한 키).
  내부 FK 는 `places.id` (BIGINT). 본 모듈이 변환을 담당한다.
- 다이어리 즐겨찾기와 달리 "하루 1개" 제약 없음. 단, UNIQUE (user_id, place_id)
  로 중복 차단 (DB 레벨).
- soft delete 미적용 — 해제는 hard delete.
"""

from __future__ import annotations

from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite_place import FavoritePlace
from models.place import Place


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────


async def _resolve_place_id(content_id: str, db: AsyncSession) -> int:
    """content_id 로 places.id 를 조회합니다.

    Args:
        content_id: 한국관광공사 콘텐츠 ID (places.content_id, UNIQUE).
        db        : AsyncSession.

    Returns:
        places.id (BIGINT).

    Raises:
        HTTPException 404: 일치하는 장소가 없는 경우.
    """
    stmt = select(Place.id).where(Place.content_id == content_id)
    place_id = (await db.execute(stmt)).scalar_one_or_none()

    if place_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"장소(content_id={content_id})를 찾을 수 없습니다.",
        )
    return place_id


# ── 공개 서비스 함수 ─────────────────────────────────────────────────────────


async def toggle_favorite_place(
    content_id: str,
    db: AsyncSession,
    current_user_id: int,
) -> tuple[bool, FavoritePlace | None]:
    """
        장소 즐겨찾기 토글.

        흐름:
            1. content_id -> places.id 변환 (404 검증)
            2. 기존 즐겨찾기 존재 확인
            3. 있으면 DELETE 후 (False, None) 반환 — 해제
               없으면 INSERT 후 (True, FavoritePlace) 반환 — 설정

        Args:
            content_id     : 한국관광공사 콘텐츠 ID
            db             : AsyncSession
            current_user_id: 현재 로그인 사용자 ID

        Returns:
            (is_favorite, favorite) 튜플.
                - is_favorite=True  : 신규 등록됨, favorite=FavoritePlace 행
                - is_favorite=False : 해제됨, favorite=None

        Raises:
            HTTPException 404: 장소 없음
    """
    place_id = await _resolve_place_id(content_id, db)

    stmt = select(FavoritePlace).where(
        FavoritePlace.user_id == current_user_id,
        FavoritePlace.place_id == place_id,
    )
    existing = (await db.execute(stmt)).scalar_one_or_none()

    if existing is not None:
        await db.execute(
            delete(FavoritePlace).where(FavoritePlace.id == existing.id)
        )
        await db.flush()
        return False, None

    favorite = FavoritePlace(user_id=current_user_id, place_id=place_id)
    db.add(favorite)
    await db.flush()
    await db.refresh(favorite)
    return True, favorite


async def list_favorite_places(
    db: AsyncSession,
    current_user_id: int,
) -> Sequence[dict]:
    """
        사용자의 즐겨찾기 장소 목록을 조회합니다.

        응답 페이로드는 셀 렌더에 필요한 최소 필드 (`content_id`, `name`,
        `sub_category`, `favorited_at`) 만 포함합니다. 이미지·주소 등 추가
        정보가 필요하면 프론트가 별도 API 로 보강.

        Args:
            db             : AsyncSession
            current_user_id: 현재 로그인 사용자 ID

        Returns:
            list[dict] — 각 항목 키: content_id, name, sub_category, favorited_at.
            정렬: favorited_at DESC (최근 즐겨찾기가 위).
    """
    stmt = (
        select(
            Place.content_id,
            Place.name,
            Place.sub_category,
            FavoritePlace.created_at,
        )
        .join(Place, FavoritePlace.place_id == Place.id)
        .where(FavoritePlace.user_id == current_user_id)
        .order_by(FavoritePlace.created_at.desc())
    )
    rows = (await db.execute(stmt)).all()
    return [
        {
            "content_id": row.content_id,
            "name": row.name,
            "sub_category": row.sub_category or "",
            "favorited_at": row.created_at,
        }
        for row in rows
    ]
