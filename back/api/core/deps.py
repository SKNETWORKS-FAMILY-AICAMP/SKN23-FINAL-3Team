# -*- coding: utf-8 -*-
"""
core/deps.py
------------
FastAPI 의존성 주입(Dependency Injection) 모듈.

제공 함수:
    - get_db()           : AsyncSession 비동기 DB 세션 (Depends 용)
    - get_current_user() : JWT 검증 후 현재 사용자 반환 (Depends 용)
    - get_optional_user(): 인증 선택적 엔드포인트용 (비로그인도 허용)

사용 예::

        @router.get("/me")
        async def read_me(
                db: AsyncSession = Depends(get_db),
                user: User = Depends(get_current_user),
        ):
                ...
"""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import AsyncSessionLocal
from core.config import settings

# Bearer 토큰 스킴 (Authorization: Bearer <token>)
_bearer = HTTPBearer(auto_error=False)


# ── DB 세션 의존성 ─────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
        FastAPI 의존성 주입용 비동기 DB 세션 생성기.

        요청당 하나의 세션을 생성하고, 요청이 끝나면 세션을 닫습니다.
        정상 처리 시 자동 commit, 예외 발생 시 자동 rollback을 수행합니다.
    """
    import core.database

    if core.database.AsyncSessionLocal is None:
        raise RuntimeError(
            "DB 세션 팩토리가 초기화되지 않았습니다. main.py lifespan에서 init_engine()을 먼저 호출하세요."
        )

    async with core.database.AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── JWT 검증 의존성 ────────────────────────────────────────────────────────
def _decode_token(token: str) -> dict:
    """
        JWT 토큰을 디코드하여 페이로드를 반환합니다.
        유효하지 않은 토큰은 401 예외를 발생시킵니다.
    """
    from jose import JWTError, jwt

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """
        Authorization 헤더의 Bearer JWT를 검증하고 현재 사용자 모델을 반환합니다.

        Raises:
                401: 토큰 없음 / 유효하지 않음
                404: 토큰의 user_id에 해당하는 사용자 없음
    """
    # 순환 임포트 방지를 위해 함수 내에서 임포트
    from models.user import User

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="인증 토큰이 필요합니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = _decode_token(credentials.credentials)
    user_id: int | None = payload.get("user_id")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰 페이로드가 올바르지 않습니다.",
        )

    result = await db.execute(
        select(User).where(User.id == user_id, User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다.",
        )

    return user


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
):
    """
        인증이 선택적인 엔드포인트에서 사용합니다.
        토큰이 없으면 None 반환, 있으면 사용자 모델 반환합니다.
    """
    if credentials is None:
        return None
    return await get_current_user(credentials=credentials, db=db)
