# -*- coding: utf-8 -*-
"""
routers/auth.py
---------------
인증 도메인 HTTP 엔드포인트.

엔드포인트:
    POST /auth/{provider}   소셜 로그인 (provider: kakao | google | naver)
                          authorization_code를 받아 자체 JWT를 반환합니다.

[흐름]
    1. 클라이언트 → 각 소셜 provider OAuth 화면에서 인증
    2. provider → authorization_code 발급 → 클라이언트가 이 엔드포인트로 전달
    3. 서버 → provider token API 호출 → provider user API 호출
    4. DB upsert → 자체 JWT 발급 → 클라이언트 반환
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db
from schemas.auth import TokenResponse
from services.auth_service import social_login

router = APIRouter(tags=["Auth"])


@router.post(
    "/{provider}",
    response_model=TokenResponse,
    summary="소셜 로그인",
    description=(
        "카카오/구글/네이버 OAuth authorization_code를 전달하면 "
        "자체 JWT 액세스 토큰을 반환합니다. "
        "`is_new_user=true` 이면 온보딩 화면으로 이동해주세요."
    ),
)
async def social_login_endpoint(
    provider: Literal["kakao", "google", "naver"],
    code: str = Query(..., description="OAuth authorization_code"),
    redirect_uri: str = Query(default="", description="OAuth 리디렉션 URI (kakao/google 필수)"),
    state: str = Query(default="", description="CSRF 검증용 state (naver 필수)"),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    result = await social_login(
        provider=provider,
        code=code,
        db=db,
        redirect_uri=redirect_uri,
        state=state,
    )
    return TokenResponse(**result)
