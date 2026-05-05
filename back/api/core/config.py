# -*- coding: utf-8 -*-
"""
core/config.py
--------------
pydantic-settings 기반 환경변수 관리 모듈.

Settings 클래스가 프로젝트 루트의 .env 파일을 자동으로 읽어
타입 검증된 설정 객체를 제공합니다.
애플리케이션 전역에서 `from core.config import settings` 로 사용합니다.
"""

from __future__ import annotations

import os

from typing import Literal
from functools import lru_cache
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """프로젝트 전역 환경변수 설정 클래스."""

    model_config = SettingsConfigDict(
        # 프로젝트 루트의 .env 파일 경로를 동적으로 계산
        env_file=os.path.join(
            os.path.dirname(__file__),   # core/
            "..", "..", "..",            # back/ → 프로젝트 루트
            ".env",
        ),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",                  # .env에 정의되지 않은 변수 무시
    )

    # ── 서버 환경 ──────────────────────────────────────────────────────────
    SERVER: Literal["local", "ec2"] = Field(default="local", alias="SERVER")
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)

    # ── RDS (MySQL) ────────────────────────────────────────────────────────
    DB_HOST: str = Field(..., description="RDS 엔드포인트")
    DB_PORT: int = Field(default=3306)
    DB_USER: str = Field(...)
    DB_PASSWORD: str = Field(...)
    DB_NAME: str = Field(default="withdog")

    # ── JWT / 관리자 공용 ──────────────────────────────────────────────────
    # SECRET_KEY는 JWT 서명 및 관리자 X-Admin-Key 인증에 함께 사용됩니다.
    SECRET_KEY: str = Field(..., description="JWT 서명 비밀키 (관리자 X-Admin-Key와 공용)")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)

    # ── AWS S3 ─────────────────────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = Field(default="")
    AWS_SECRET_ACCESS_KEY: str = Field(default="")
    AWS_S3_BUCKET_NAME: str = Field(default="withdog-storage")
    AWS_REGION: str = Field(default="ap-northeast-2")

    # ── 소셜 로그인 (OAuth2) ────────────────────────────────────────────────
    GOOGLE_CLIENT_ID: str = Field(default="")
    GOOGLE_CLIENT_SECRET: str = Field(default="")
    # Android InstalledApp client (PKCE 기반, client_secret 없음).
    # 모바일 앱이 `flutter_appauth` 로 발급한 code 를 백엔드가 token 교환할 때 사용.
    GOOGLE_ANDROID_CLIENT_ID: str = Field(default="")
    KAKAO_CLIENT_ID: str = Field(default="")
    KAKAO_CLIENT_SECRET: str = Field(default="")
    NAVER_CLIENT_ID: str = Field(default="")
    NAVER_CLIENT_SECRET: str = Field(default="")

    # ── SSH 터널 (local 환경 전용) ──────────────────────────────────────────
    SSH_HOST: str = Field(default="")
    SSH_PORT: int = Field(default=22)
    SSH_USER: str = Field(default="ubuntu")
    SSH_PKEY: str = Field(default="")

    # ── OpenAI ───────────────────────────────────────────────────────────────
    OPENAI_API_KEY: str = Field(default="")
    GPT_MODEL: str = Field(default="gpt-4.1-mini")
    GPT_IMAGE_MODEL: str = Field(default="gpt-image-1")
    # ── 외부 API ──────────────────────────────────────────────────────────
    KAKAO_REST_API_KEY: str = Field(default="", description="카카오 REST API 키 (랜드마크 좌표 조회용)")

    # ── 개발 모드 플래그 ─────────────────────────────────────────────────────
    USE_DUMMY_PLACES: bool = Field(default=False)

    # ── 계산된 필드 ─────────────────────────────────────────────────────────
    @computed_field  # type: ignore[misc]
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """
                aiomysql 드라이버 기반 비동기 DB URL.
                local 모드에서는 SSH 터널이 열린 뒤 호출해야 정확한 포트가 적용됩니다.
                (터널 포트는 앱 시작 시 동적으로 결정되므로 main.py lifespan에서 처리)
        """
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    """싱글턴 Settings 인스턴스 반환 (최초 1회만 생성)."""
    return Settings()


# 전역 settings 객체 — 모든 모듈에서 이 객체를 임포트하여 사용
settings: Settings = get_settings()
