# -*- coding: utf-8 -*-
"""
services/auth.py
----------------
소셜 로그인(카카오 / 구글 / 네이버) 처리 및 자체 JWT 발급/검증 서비스.

[흐름]
1. 클라이언트가 각 provider OAuth 인증 완료 후 authorization_code 전달
2. 서버가 provider token API 호출 → access_token 발급
3. provider user API 호출 → email, provider_id 등 사용자 정보 획득
4. DB에서 (provider, provider_id)로 사용자 조회
   - 신규: 최소 정보로 생성 (upsert)
   - 기존: 그대로 반환
5. 자체 JWT(HS256) 발급 → 클라이언트에 반환
6. 이후 모든 요청은 Authorization: Bearer {JWT} 로 인증

주요 함수:
    - social_login()     : provider별 로그인 처리 진입점
    - create_jwt()       : 자체 JWT 액세스 토큰 생성
    - verify_jwt()       : JWT 검증 및 페이로드 반환
    - _fetch_kakao_user(): 카카오 사용자 정보 조회
    - _fetch_google_user(): 구글 사용자 정보 조회
    - _fetch_naver_user(): 네이버 사용자 정보 조회
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Literal

import httpx
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings

# ── 지원하는 소셜 로그인 Provider 타입 ────────────────────────────────────
Provider = Literal["kakao", "google", "naver"]


# =============================================================================
# JWT 유틸리티
# =============================================================================

def create_jwt(user_id: int, provider: str) -> str:
    """
        자체 JWT 액세스 토큰을 생성합니다.

        Args:
                user_id : DB의 users.id
                provider: 소셜 로그인 제공자 (kakao / google / naver)

        Returns:
                HS256 서명된 JWT 문자열
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload: dict[str, Any] = {
        "user_id": user_id,
        "provider": provider,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_jwt(token: str) -> dict[str, Any]:
    """
        JWT 토큰을 검증하고 페이로드를 반환합니다.

        Raises:
                HTTPException 401: 유효하지 않거나 만료된 토큰
    """
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"토큰 검증 실패: {e}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# =============================================================================
# Provider별 사용자 정보 조회
# =============================================================================

async def _exchange_kakao_token(code: str, redirect_uri: str) -> str:
    """카카오 authorization_code → access_token 교환."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://kauth.kakao.com/oauth/token",
            data={
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_CLIENT_ID,
                "client_secret": settings.KAKAO_CLIENT_SECRET,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def _fetch_kakao_user(access_token: str) -> dict[str, str]:
    """
        카카오 API로 사용자 정보를 조회합니다.

        Returns:
                {"provider_id": str, "email": str, "nickname": str}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    resp.raise_for_status()
    data = resp.json()

    kakao_account = data.get("kakao_account", {})
    profile = kakao_account.get("profile", {})

    return {
        "provider_id": str(data["id"]),
        "email": kakao_account.get("email", ""),
        "nickname": profile.get("nickname", "kakao_user"),
    }


async def _exchange_google_token(code: str, redirect_uri: str) -> str:
    """구글 authorization_code → access_token 교환."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def _fetch_google_user(access_token: str) -> dict[str, str]:
    """
        구글 API로 사용자 정보를 조회합니다.

        Returns:
                {"provider_id": str, "email": str, "nickname": str}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    resp.raise_for_status()
    data = resp.json()

    return {
        "provider_id": str(data["id"]),
        "email": data.get("email", ""),
        "nickname": data.get("name", "google_user"),
    }


async def _exchange_naver_token(code: str, state: str) -> str:
    """네이버 authorization_code → access_token 교환."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://nid.naver.com/oauth2.0/token",
            params={
                "grant_type": "authorization_code",
                "client_id": settings.NAVER_CLIENT_ID,
                "client_secret": settings.NAVER_CLIENT_SECRET,
                "code": code,
                "state": state,
            },
        )
    resp.raise_for_status()
    return resp.json()["access_token"]


async def _fetch_naver_user(access_token: str) -> dict[str, str]:
    """
        네이버 API로 사용자 정보를 조회합니다.

        Returns:
                {"provider_id": str, "email": str, "nickname": str}
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    resp.raise_for_status()
    data = resp.json()["response"]

    return {
        "provider_id": str(data["id"]),
        "email": data.get("email", ""),
        "nickname": data.get("nickname", data.get("name", "naver_user")),
    }


# =============================================================================
# 소셜 로그인 통합 진입점
# =============================================================================

async def social_login(
    provider: Provider,
    code: str,
    db: AsyncSession,
    redirect_uri: str = "",
    state: str = "",
) -> dict[str, str]:
    """
        소셜 로그인을 처리하고 자체 JWT를 반환합니다.

        [처리 순서]
        1. provider별 token 교환 → access_token 획득
        2. provider user API 호출 → {provider_id, email, nickname} 획득
        3. DB에서 (provider, provider_id) 조회 → 없으면 신규 생성(upsert)
        4. 자체 JWT 발급 후 반환

        Args:
                provider    : "kakao" | "google" | "naver"
                code        : OAuth authorization_code
                db          : AsyncSession (Depends(get_db)로 주입)
                redirect_uri: OAuth 리디렉션 URI (kakao/google 필수)
                state       : CSRF 검증용 state 파라미터 (naver 필수)

        Returns:
                {"access_token": str, "token_type": "bearer", "is_new_user": bool}

        Raises:
                HTTPException 400: 지원하지 않는 provider
                HTTPException 502: provider API 호출 실패
    """
    # 순환 import 방지
    from models.user import User

    # ── Step 1 & 2: provider별 사용자 정보 조회 ─────────────────────────────
    try:
        if provider == "kakao":
            token = await _exchange_kakao_token(code, redirect_uri)
            user_info = await _fetch_kakao_user(token)
        elif provider == "google":
            token = await _exchange_google_token(code, redirect_uri)
            user_info = await _fetch_google_user(token)
        elif provider == "naver":
            token = await _exchange_naver_token(code, state)
            user_info = await _fetch_naver_user(token)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"지원하지 않는 provider: {provider}",
            )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{provider} API 호출 실패: {e}",
        )

    provider_id: str = user_info["provider_id"]
    email: str = user_info["email"]
    nickname: str = user_info["nickname"]

    # ── Step 3: DB 조회 → upsert ─────────────────────────────────────────────
    result = await db.execute(
        select(User).where(
            User.provider == provider,
            User.provider_id == provider_id,
        )
    )
    user = result.scalar_one_or_none()
    is_new_user = user is None

    if is_new_user:
        # 신규 사용자: 최소 정보로 생성
        # profile_id, type_id는 온보딩에서 입력
        user = User(
            email=email,
            nickname=nickname,
            provider=provider,
            provider_id=provider_id,
        )
        db.add(user)
        await db.flush()   # id 생성을 위한 flush (commit은 get_db()에서)

    # ── Step 4: 자체 JWT 발급 ────────────────────────────────────────────────
    access_token = create_jwt(user_id=user.id, provider=provider)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "is_new_user": is_new_user,
    }
