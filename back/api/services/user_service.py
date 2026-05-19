# -*- coding: utf-8 -*-
"""
services/user.py
----------------
사용자 도메인 서비스 레이어 (DB 쿼리 + 비즈니스 로직 통합).

주요 함수:
    - get_user()    : 단건 조회 (deleted_at IS NULL)
    - update_user() : 프로필 수정 (본인 확인 + FK 무결성 + type_id 자동 재계산)
    - delete_user() : Soft Delete (본인 확인 → deleted_at 기록)

소셜 로그인 upsert 로직은 services/auth.py의 social_login()에 통합되어 있습니다.

[소유권 정책]
프로필 수정 및 탈퇴는 본인만 가능합니다.
관리자 권한이 필요한 경우 별도 admin 라우터로 분리할 것을 권장합니다.

[type_id 정책 — DANG-141 후속, 2026-05-12]
type_id 는 클라이언트 입력값이 아닌 selected_tags 로부터 OwnerScorer.classify_type()
으로 자동 계산되는 파생 필드입니다. selected_tags 가 빈 배열이면 type_id = NULL.
"""

from __future__ import annotations

from models.user import User
from models.pet import Pet
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from core.utils import kst_now
from models.image import Image
from models.keyword import Keyword
from schemas.user import UserUpdate
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from utils.profanity_filter import contains_profanity


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────

def _assert_owner(user: User, current_user_id: int) -> None:
    """
        요청자가 해당 사용자 본인인지 검증합니다.

        Raises:
                HTTPException 403: 본인 계정이 아닌 경우
    """
    if user.id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 계정만 수정/삭제할 수 있습니다.",
        )


async def _verify_image_exists(image_id: int, db: AsyncSession) -> None:
    """profile_id FK: 이미지가 존재하는지 검증합니다."""

    result = await db.execute(
        select(Image).where(
            Image.id == image_id,
            Image.deleted_at.is_(None),
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"프로필 이미지(id={image_id})를 찾을 수 없습니다.",
        )


def _get_owner_scorer(request: Request):
    """app.state.ai_container 에서 OwnerScorer 싱글톤을 꺼낸다.

    AIContainer 초기화는 main.py lifespan 에서 수행되며 실패 시 503.
    """
    container = getattr(request.app.state, "ai_container", None)
    if container is None or not hasattr(container, "_owner_scorer"):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="성향 점수 모듈 미준비",
        )
    return container._owner_scorer


async def _resolve_user_type_id(type_key: str, db: AsyncSession) -> int:
    """OwnerScorer.classify_type() 반환 영문 type_key → keywords.id 매핑.

    Args:
        type_key: 영문 type_key (예: "nature_lover").
        db     : AsyncSession.

    Returns:
        keywords.id (int).

    Raises:
        HTTPException 500: USER_TYPE 카테고리에 매칭 row 없음
            (migrate_profile_types.py 미실행 의심).
    """
    result = await db.execute(
        select(Keyword.id).where(
            Keyword.category == "USER_TYPE",
            Keyword.description == type_key,
        )
    )
    keyword_id = result.scalar_one_or_none()
    if keyword_id is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                f"USER_TYPE 키워드(description={type_key}) 미존재. "
                "migrate_profile_types.py 실행 여부를 확인하세요."
            ),
        )
    return keyword_id


async def _verify_primary_pet_ownership(
    pet_id: int,
    user_id: int,
    db: AsyncSession,
) -> None:
    """primary_pet_id FK: 본인 소유의 활성 반려견인지 검증합니다.

    Args:
        pet_id : 대표로 지정하려는 반려견 ID.
        user_id: 현재 로그인 사용자 ID (소유 검증용).
        db     : AsyncSession.

    Raises:
        HTTPException 404: pets 에 존재하지 않거나 soft-deleted 된 반려견.
        HTTPException 403: 본인 소유가 아닌 반려견.
    """
    result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.deleted_at.is_(None))
    )
    pet = result.scalar_one_or_none()

    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"반려견(id={pet_id})을 찾을 수 없습니다.",
        )
    if pet.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 반려견만 대표로 설정할 수 있습니다.",
        )


# ── 공개 서비스 함수 ─────────────────────────────────────────────────────────

async def get_user(user_id: int, db: AsyncSession) -> User:
    """
        사용자 단건 조회.

        Args:
                user_id: 조회할 사용자 ID
                db     : AsyncSession

        Returns:
                User ORM 객체 (deleted_at IS NULL)

        Raises:
                HTTPException 404: 존재하지 않거나 탈퇴한 사용자
    """
    result = await db.execute(
        select(User)
        .where(User.id == user_id, User.deleted_at.is_(None))
        .options(
            selectinload(User.profile),
            selectinload(User.primary_pet).selectinload(Pet.image),
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"사용자(id={user_id})를 찾을 수 없습니다.",
        )

    return user


async def update_user(
    user_id: int,
    data: UserUpdate,
    request: Request,
    db: AsyncSession,
    current_user_id: int,
) -> User:
    """
        사용자 프로필을 수정합니다.

        [PATCH 시맨틱]
        - 요청 바디에서 제공된 필드만 업데이트합니다.
        - 제공되지 않은 필드는 기존 값을 유지합니다.

        [FK 무결성 검증]
        - profile_id 변경 시 images 테이블 참조 확인
        - primary_pet_id 변경 시 본인 소유 활성 반려견 확인

        [type_id 자동 재계산]
        selected_tags 가 들어오면 OwnerScorer.classify_type() 결과로 type_id 를
        자동 재계산합니다 (빈 배열 → NULL). 클라이언트가 직접 보낸 type_id 는
        무시됩니다 (파생 필드 정책).

        Args:
                user_id        : 수정할 사용자 ID
                data           : 수정 데이터 (UserUpdate)
                request        : FastAPI Request (app.state.ai_container 접근용)
                db             : AsyncSession
                current_user_id: 현재 로그인 사용자 ID (소유권 검증용)

        Returns:
                수정된 User ORM 객체

        Raises:
                HTTPException 403: 본인 계정이 아님
                HTTPException 404: 사용자/이미지/반려견 없음
                HTTPException 500: USER_TYPE 키워드 행 누락
                HTTPException 503: AIContainer 미초기화
    """
    user = await get_user(user_id, db)
    _assert_owner(user, current_user_id)

    # 변경된 필드만 추출 (model_dump exclude_unset=True)
    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        return user  # 변경 사항 없음

    # 욕설 필터 (닉네임 — 정책 #71)
    if "nickname" in update_data and contains_profanity(update_data["nickname"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="부적절한 단어가 포함되어 있습니다",
        )

    # selected_tags 기반 type_id 자동 재계산 (PATCH 시맨틱).
    # 키 미존재 → type_id 미변경. 빈 배열 → NULL. 채워짐 → classify.
    if "selected_tags" in update_data:
        tags = update_data["selected_tags"] or []
        if tags:
            scorer = _get_owner_scorer(request)
            type_key = scorer.classify_type(tags)
            update_data["type_id"] = await _resolve_user_type_id(type_key, db)
        else:
            update_data["type_id"] = None

    # FK 무결성 검증
    if "profile_id" in update_data:
        await _verify_image_exists(update_data["profile_id"], db)

    if "primary_pet_id" in update_data and update_data["primary_pet_id"] is not None:
        await _verify_primary_pet_ownership(
            update_data["primary_pet_id"], current_user_id, db
        )

    # ORM 필드 업데이트
    for field, value in update_data.items():
        setattr(user, field, value)

    # updated_at은 onupdate=kst_now 로 자동 반영
    await db.flush()

    # selectinload 로 profile / primary_pet.image 를 확실하게 로드
    return await get_user(user_id, db)


async def delete_user(
    user_id: int,
    db: AsyncSession,
    current_user_id: int,
) -> None:
    """
        사용자 Soft Delete (회원 탈퇴).

        deleted_at에 현재 시각을 기록합니다.
        10일 후 services/scheduler.py의 hard_delete_withdrawn_users()가 물리 삭제합니다.

        [provider_id mangle — 2026-05-12]
        탈퇴 즉시 provider_id 에 `__deleted_<timestamp>` suffix 를 박아 동일 소셜
        계정으로 재가입 시 UNIQUE (provider, provider_id) 충돌을 회피합니다.
        재가입 정책 = 새 users.id 로 신규 계정 생성, 기존 데이터 미연결.

        Args:
                user_id        : 탈퇴할 사용자 ID
                db             : AsyncSession
                current_user_id: 현재 로그인 사용자 ID (소유권 검증용)

        Raises:
                HTTPException 403: 본인 계정이 아님
                HTTPException 404: 사용자 없음
    """
    user = await get_user(user_id, db)
    _assert_owner(user, current_user_id)

    user.deleted_at = kst_now()
    # 동일 소셜 계정 재가입 시 UNIQUE uq_users_provider (provider, provider_id) 충돌 회피.
    # 10일 후 hard delete 시 row 자체가 사라지므로 영구 잔존 X.
    ts = int(user.deleted_at.timestamp())
    user.provider_id = f"{user.provider_id}__deleted_{ts}"
    await db.flush()
