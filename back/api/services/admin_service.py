# -*- coding: utf-8 -*-
"""
services/admin_service.py
-------------------------
관리자 전용 서비스.

주요 함수:
    - create_permanent_jwt() : 유효기간 없는 JWT 액세스 토큰 생성
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from jose import jwt

from core.config import settings


def create_permanent_jwt(user_id: int, provider: str = "admin") -> str:
    """
    유효기간(exp)이 없는 영구 JWT 액세스 토큰을 생성합니다.
    관리자 테스트/개발 용도로만 사용하세요.

    Args:
        user_id : DB의 users.id
        provider: 토큰에 기록할 provider 문자열 (기본값 "admin")

    Returns:
        HS256 서명된 JWT 문자열 (exp 클레임 없음)
    """
    payload: dict[str, Any] = {
        "user_id": user_id,
        "provider": provider,
        "iat": datetime.now(timezone.utc),
        "permanent": True,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
