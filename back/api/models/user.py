# -*- coding: utf-8 -*-
"""
models/user.py
--------------
users 테이블 ORM 모델.

소셜 로그인(카카오/구글/네이버) 기반 사용자 계정.
- profile_id: images.id FK (프로필 이미지)
- type_id   : keywords.id FK (대표 성향 키워드)
- Soft Delete: deleted_at 기록 → 10일 후 Hard Delete (scheduler.py)
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class GenderEnum(str, enum.Enum):
    """성별 Enum."""
    MALE = "MALE"
    FEMALE = "FEMALE"


class User(Base):
    """소셜 로그인 사용자 계정."""

    __tablename__ = "users"
    __table_args__ = (
        # 소셜 로그인 중복 가입 방지
        UniqueConstraint("provider", "provider_id", name="uq_users_provider"),
        # 이메일 조회 인덱스
        Index("idx_users_email", "email"),
        {
            "comment": "소셜 로그인 사용자 계정",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="사용자 ID")
    email: Mapped[str] = mapped_column(String(255), nullable=False, comment="이메일 주소")
    nickname: Mapped[str] = mapped_column(String(50), nullable=False, comment="닉네임")
    gender: Mapped[GenderEnum | None] = mapped_column(SAEnum(GenderEnum), nullable=True, comment="성별")
    age: Mapped[int | None] = mapped_column(TINYINT(unsigned=True), nullable=True, comment="나이")

    # FK → images
    profile_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("images.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
        comment="프로필 이미지 ID",
    )

    provider: Mapped[str] = mapped_column(String(20), nullable=False, comment="소셜 로그인 제공자 (google/kakao/naver)")
    provider_id: Mapped[str] = mapped_column(String(255), nullable=False, comment="OAuth2.0 제공자 발급 고유 ID")

    # FK → keywords
    type_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("keywords.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
        comment="대표 성향 키워드 ID",
    )

    selected_tags: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, comment="선택한 여행 성향 태그 목록")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=datetime.utcnow, server_default=func.now(),
        comment="생성 일시",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now(),
        comment="최종 수정 일시",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="탈퇴 일시")

    # ── Relationships ──────────────────────────────────────────────────────
    profile: Mapped[Image] = relationship("Image", foreign_keys=[profile_id], lazy="select")
    keyword: Mapped[Keyword] = relationship("Keyword", foreign_keys=[type_id], lazy="select")
    pets: Mapped[list[Pet]] = relationship("Pet", back_populates="user", cascade="all, delete-orphan")
    chat_rooms: Mapped[list[ChatRoom]] = relationship("ChatRoom", back_populates="user", cascade="all, delete-orphan")
    diaries: Mapped[list[Diary]] = relationship("Diary", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} provider={self.provider!r}>"
