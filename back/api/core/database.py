# -*- coding: utf-8 -*-
"""
core/database.py
----------------
SQLAlchemy 2.0 비동기 DB 엔진 및 세션 설정 모듈.

제공 객체:
    - engine          : AsyncEngine (aiomysql 드라이버)
    - AsyncSessionLocal : async_sessionmaker 팩토리
    - Base            : DeclarativeBase (모든 ORM 모델의 부모 클래스)
    - init_db()       : 앱 시작 시 테이블 자동 생성 (개발 환경용)

local 환경에서는 SSH 터널이 먼저 열린 뒤 엔진을 생성해야 합니다.
main.py의 lifespan에서 터널을 시작한 후 create_engine()을 호출합니다.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from core.config import settings

# ── ORM 베이스 클래스 ──────────────────────────────────────────────────────
class Base(AsyncAttrs, DeclarativeBase):
    """
        모든 SQLAlchemy ORM 모델이 상속받는 베이스 클래스.
        AsyncAttrs 믹스인을 포함하여 비동기 lazy-load를 지원합니다.
    """
    pass


# ── 엔진 & 세션 팩토리 (지연 초기화) ──────────────────────────────────────
_engine: AsyncEngine | None = None
AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None


def _build_url(host: str, port: int) -> str:
    """aiomysql 연결 URL을 생성합니다."""
    return (
        f"mysql+aiomysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
        f"@{host}:{port}/{settings.DB_NAME}"
        f"?charset=utf8mb4"
    )


def init_engine(host: str | None = None, port: int | None = None) -> AsyncEngine:
    """
        AsyncEngine을 생성하여 모듈 전역에 등록합니다.

        Args:
                host: DB 호스트 (local 모드에서는 '127.0.0.1')
                port: DB 포트 (local 모드에서는 SSH 터널 바인딩 포트)

        Returns:
                생성된 AsyncEngine 객체
    """
    global _engine, AsyncSessionLocal

    _host = host or settings.DB_HOST
    _port = port or settings.DB_PORT

    _engine = create_async_engine(
        _build_url(_host, _port),
        pool_pre_ping=True,      # 끊긴 커넥션 자동 재확인
        pool_recycle=1800,       # 30분마다 커넥션 재생성
        pool_size=10,            # 커넥션 풀 크기
        max_overflow=20,         # 풀 초과 허용 커넥션 수
        echo=settings.DEBUG,     # DEBUG=True 시 SQL 로그 출력
    )

    AsyncSessionLocal = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,  # commit 후 객체 만료 방지
    )

    return _engine


def get_engine() -> AsyncEngine:
    """현재 등록된 AsyncEngine을 반환합니다. 미초기화 시 예외 발생."""
    if _engine is None:
        raise RuntimeError(
            "DB 엔진이 초기화되지 않았습니다. "
            "main.py lifespan에서 init_engine()을 먼저 호출하세요."
        )
    return _engine


async def init_db() -> None:
    """
        앱 시작 시 모든 ORM 모델 테이블을 생성합니다.
        (이미 존재하는 테이블은 건너뜀. 개발/테스트 환경 권장)
    """
    engine = get_engine()
    async with engine.begin() as conn:
        # models 패키지를 임포트해야 Base.metadata에 테이블이 등록됩니다.
        import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """앱 종료 시 DB 커넥션 풀을 정상 해제합니다."""
    if _engine is not None:
        await _engine.dispose()
