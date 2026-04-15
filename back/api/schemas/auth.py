# -*- coding: utf-8 -*-
"""
schemas/auth.py
---------------
인증 도메인 Pydantic v2 스키마.

TokenResponse: 소셜 로그인 후 JWT 응답 스키마
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TokenResponse(BaseModel):
    """소셜 로그인 성공 응답 — 자체 JWT 액세스 토큰 반환."""

    access_token: str = Field(..., description="JWT 액세스 토큰")
    token_type: str = Field(default="bearer", description="토큰 타입")
    is_new_user: bool = Field(..., description="최초 로그인(신규 가입) 여부")
