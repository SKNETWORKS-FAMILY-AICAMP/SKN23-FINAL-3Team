# -*- coding: utf-8 -*-
"""
routers/admin_router.py
-----------------------
관리자 전용 HTTP 엔드포인트.

엔드포인트:
    GET /admin/token    유효기간 없는 영구 JWT 발급
                        X-Admin-Key 헤더로 관리자 인증 후 user_id를 받아 토큰 반환

[보안]
    .env 의 SECRET_KEY 값을 X-Admin-Key 헤더로 전달해야 합니다.
    SECRET_KEY 설정되지 않은 경우 모든 요청을 거부합니다.
"""

from __future__ import annotations

from fastapi import Depends
from core.deps import get_db
from sqlalchemy import select
from core.config import settings
from schemas.auth import TokenResponse
from sqlalchemy.ext.asyncio import AsyncSession
from services.admin_service import create_permanent_jwt
from fastapi import APIRouter, Header, HTTPException, Query, status

router = APIRouter(tags=["Admin"])


def _verify_admin_key(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")) -> None:
    """X-Admin-Key 헤더가 SECRET_KEY와 일치하는지 검증합니다."""
    if not settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SECRET_KEY 설정되지 않았습니다. .env를 확인하세요.",
        )
    if x_admin_key != settings.SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="유효하지 않은 관리자 키입니다.",
        )


@router.get(
    "/token",
    response_model=TokenResponse,
    summary="관리자용 영구 토큰 발급",
    description=(
        "**관리자 전용** — `X-Admin-Key` 헤더 인증 후 유효기간 없는 JWT를 발급합니다.\n\n"
        "- `user_id`: 토큰을 발급할 사용자 ID (DB의 `users.id`)\n"
        "- `provider`: 토큰에 기록할 provider 문자열 (기본값 `admin`)\n\n"
        "> ⚠️ 개발/테스트 용도로만 사용하세요."
    ),
)
async def issue_permanent_token(
    user_id: int = Query(..., description="토큰을 발급할 사용자 ID (users.id)"),
    provider: str = Query(default="admin", description="provider 레이블 (기본값: admin)"),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(_verify_admin_key),
) -> TokenResponse:
    from models.user import User

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user_id={user_id} 에 해당하는 사용자를 찾을 수 없습니다.",
        )

    access_token = create_permanent_jwt(user_id=user.id, provider=provider)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        is_new_user=False,
    )
