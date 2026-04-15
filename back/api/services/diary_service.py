# -*- coding: utf-8 -*-
"""
services/diary.py
-----------------
다이어리 도메인 서비스 레이어 (DB 쿼리 + 비즈니스 로직 통합).

주요 함수:
    - create_diary() : 다이어리 생성 (pet_id / image_id FK 검증)
    - list_diaries() : 목록 조회 (user_id / pet_id 필터, deleted_at IS NULL)
    - get_diary()    : 단건 조회
    - update_diary() : 수정 (image_id 바인딩 포함, 본인 확인)
    - delete_diary() : Soft Delete (본인 확인)

[2-phase 저장]
 1단계: image_id 없이 생성 → AI 파이프라인 병렬 실행
 2단계: AI 이미지 완성 후 update_diary()로 image_id 바인딩 (PATCH)

[소유권 정책]
다이어리의 수정 · 삭제는 작성자(diary.user_id == current_user_id) 본인만 가능합니다.
"""

from __future__ import annotations

from datetime import datetime
from core.utils import kst_now
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.diary import Diary
from schemas.diary import DiaryCreate, DiaryUpdate


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────

def _assert_owner(diary: Diary, current_user_id: int) -> None:
    """요청자가 해당 다이어리의 작성자인지 검증합니다."""
    if diary.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 다이어리만 수정/삭제할 수 있습니다.",
        )


async def _verify_pet(pet_id: int, user_id: int, db: AsyncSession) -> None:
    """pet_id FK: 반려동물이 존재하며 해당 사용자의 것인지 검증합니다."""
    from models.pet import Pet

    result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.deleted_at.is_(None))
    )
    pet = result.scalar_one_or_none()

    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"반려동물(id={pet_id})을 찾을 수 없습니다.",
        )
    if pet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 반려동물만 다이어리에 등록할 수 있습니다.",
        )


async def _verify_image(image_id: int, db: AsyncSession) -> None:
    """image_id FK: 이미지가 존재하는지 검증합니다."""
    from models.image import Image

    result = await db.execute(
        select(Image).where(
            Image.id == image_id,
            Image.deleted_at.is_(None),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"이미지(id={image_id})를 찾을 수 없습니다.",
        )


# ── 공개 서비스 함수 ─────────────────────────────────────────────────────────

async def create_diary(
    data: DiaryCreate,
    db: AsyncSession,
    current_user_id: int,
) -> Diary:
    """
        다이어리를 생성합니다.

        [2-phase 저장 1단계]
        image_id 없이 먼저 저장하면 AI 파이프라인이 병렬로 실행됩니다.
        AI 이미지 완성 후 update_diary()로 image_id를 바인딩합니다.

        Args:
                data           : DiaryCreate 요청 데이터
                db             : AsyncSession
                current_user_id: 현재 로그인 사용자 ID

        Returns:
                생성된 Diary ORM 객체

        Raises:
                HTTPException 403: pet이 본인 소유 아님
                HTTPException 404: pet / image 없음
    """
    # FK 검증
    await _verify_pet(data.pet_id, current_user_id, db)

    if data.image_id is not None:
        await _verify_image(data.image_id, db)

    diary = Diary(
        user_id=current_user_id,
        pet_id=data.pet_id,
        image_id=data.image_id,
        when_text=data.when_text,
        where_text=data.where_text,
        who_text=data.who_text,
        what_text=data.what_text,
        how_text=data.how_text,
        why_text=data.why_text,
        title=data.title,
        content=data.content,
        summary=data.summary,
        emotion=data.emotion,
    )
    db.add(diary)
    await db.flush()
    await db.refresh(diary)

    return diary


async def list_diaries(
    db: AsyncSession,
    *,
    user_id: int | None = None,
    pet_id: int | None = None,
) -> Sequence[Diary]:
    """
        다이어리 목록을 조회합니다.

        - user_id: 사용자별 필터 (created_at DESC)
        - pet_id : 반려동물별 추가 필터
        - 두 파라미터 동시 사용 가능 (AND 조건)
        - deleted_at IS NULL 기본 적용

        Args:
                db     : AsyncSession
                user_id: 조회할 사용자 ID (선택)
                pet_id : 조회할 반려동물 ID (선택)

        Returns:
                Diary ORM 객체 목록 (created_at DESC)
    """
    stmt = select(Diary).where(Diary.deleted_at.is_(None))

    if user_id is not None:
        stmt = stmt.where(Diary.user_id == user_id)

    if pet_id is not None:
        stmt = stmt.where(Diary.pet_id == pet_id)

    stmt = stmt.order_by(Diary.created_at.desc())

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_diary(diary_id: int, db: AsyncSession) -> Diary:
    """
        다이어리 단건 조회.

        Raises:
                HTTPException 404: 존재하지 않거나 삭제된 다이어리
    """
    result = await db.execute(
        select(Diary).where(
            Diary.id == diary_id,
            Diary.deleted_at.is_(None),
        )
    )
    diary = result.scalar_one_or_none()

    if diary is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"다이어리(id={diary_id})를 찾을 수 없습니다.",
        )

    return diary


async def update_diary(
    diary_id: int,
    data: DiaryUpdate,
    db: AsyncSession,
    current_user_id: int,
) -> Diary:
    """
        다이어리를 수정합니다.

        [2-phase 저장 2단계]
        AI 이미지 완성 후 image_id를 이 함수로 바인딩합니다.

        제공된 필드만 업데이트합니다 (PATCH 시맨틱).
        pet_id / image_id 변경 시 FK 무결성 검증을 수행합니다.

        Raises:
                HTTPException 403: 본인 다이어리 아님
                HTTPException 404: 다이어리 / pet / image 없음
    """
    diary = await get_diary(diary_id, db)
    _assert_owner(diary, current_user_id)

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        return diary

    # FK 무결성 검증
    if "pet_id" in update_data:
        await _verify_pet(update_data["pet_id"], current_user_id, db)

    if "image_id" in update_data and update_data["image_id"] is not None:
        await _verify_image(update_data["image_id"], db)

    for field, value in update_data.items():
        setattr(diary, field, value)

    await db.flush()
    await db.refresh(diary)

    return diary


async def delete_diary(
    diary_id: int,
    db: AsyncSession,
    current_user_id: int,
) -> None:
    """
        다이어리 Soft Delete.

        Raises:
                HTTPException 403: 본인 다이어리 아님
                HTTPException 404: 다이어리 없음
    """
    diary = await get_diary(diary_id, db)
    _assert_owner(diary, current_user_id)

    diary.deleted_at = kst_now()
    await db.flush()
