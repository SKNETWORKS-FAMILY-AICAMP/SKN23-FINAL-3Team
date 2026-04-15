# -*- coding: utf-8 -*-
"""
routers/users.py
----------------
사용자 도메인 HTTP 엔드포인트.

엔드포인트:
    GET    /users/me            JWT 기반 현재 로그인 사용자 조회
    GET    /users/{user_id}     사용자 단건 조회 (인증 필요)
    PATCH  /users/{user_id}     프로필 수정 (본인만 가능)
    DELETE /users/{user_id}     회원 탈퇴 Soft Delete (본인만  가능)

[소셜 로그인]
    POST /auth/{provider}  →  routers/auth.py 에서 처리

[주의]
    /users/me 는 /users/{user_id} 보다 먼저 등록해야 라우팅이 올바르게 동작합니다.
    FastAPI는 경로를 등록 순서대로 매칭하므로 순서가 중요합니다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from models.user import User
from schemas.user import UserResponse, UserUpdate
from services import user_service as user_svc

router = APIRouter(tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="현재 로그인 사용자 조회",
    description="Authorization 헤더의 JWT를 검증하여 현재 사용자 정보를 반환합니다.",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """JWT 기반으로 로그인 사용자 본인 정보를 반환합니다."""
    return UserResponse.model_validate(current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="사용자 단건 조회",
)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),   # 인증 필요 (본인 제한 없음)
) -> UserResponse:
    """user_id로 사용자를 조회합니다. 탈퇴 사용자는 404를 반환합니다."""
    user = await user_svc.get_user(user_id, db)
    return UserResponse.model_validate(user)


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
    summary="사용자 프로필 수정",
    description=(
        "제공된 필드만 업데이트합니다 (PATCH 시맨틱).\n\n"
        "- `profile_id` 변경 시 images 테이블 참조 검증\n"
        "- `type_id` 변경 시 keywords 테이블 참조 검증\n"
        "- **본인 계정만 수정 가능** (다른 user_id 접근 시 403)"
    ),
)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    user = await user_svc.update_user(
        user_id=user_id,
        data=data,
        db=db,
        current_user_id=current_user.id,
    )
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="회원 탈퇴 (Soft Delete)",
    description=(
        "`deleted_at`에 현재 시각을 기록합니다.\n\n"
        "10일 후 APScheduler 배치(`hard_delete_withdrawn_users`)가 물리 삭제합니다.\n\n"
        "**본인 계정만 삭제 가능** (다른 user_id 접근 시 403)"
    ),
)
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await user_svc.delete_user(
        user_id=user_id,
        db=db,
        current_user_id=current_user.id,
    )
