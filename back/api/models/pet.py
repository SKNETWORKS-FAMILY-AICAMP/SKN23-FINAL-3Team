# -*- coding: utf-8 -*-
"""
models/pet.py
-------------
pets 테이블 ORM 모델.

반려동물 기본 정보.
- user_id  : users.id FK
- breed_id : breeds.id FK
- type_id  : keywords.id FK (대표 성격 키워드)
- Soft Delete: deleted_at 기록
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    JSON,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class PetGenderEnum(str, enum.Enum):
    """반려동물 성별 Enum."""
    MALE = "MALE"
    FEMALE = "FEMALE"


class Pet(Base):
    """반려동물 기본 정보."""

    __tablename__ = "pets"
    __table_args__ = (
        Index("idx_pets_user_id", "user_id"),
        {
            "comment": "반려동물 기본 정보",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="반려동물 ID")

    # FK → users
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        comment="사용자 ID",
    )

    # FK → breeds
    breed_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("breeds.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        comment="견종 ID",
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="반려동물 이름")
    birth_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, comment="생년월일")
    gender: Mapped[PetGenderEnum] = mapped_column(SAEnum(PetGenderEnum), nullable=False, comment="성별")
    is_neutered: Mapped[bool | None] = mapped_column(Boolean, nullable=True, comment="중성화 여부 (NULL=미입력)")

    # FK → keywords
    type_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("keywords.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=False,
        comment="대표 성격 키워드 ID",
    )

    selected_tags: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, comment="선택한 성격 태그 목록")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=datetime.utcnow, server_default=func.now(),
        comment="등록 일시",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now(),
        comment="수정 일시",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="삭제 일시")

    # ── Relationships ──────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="pets")
    breed: Mapped[Breed] = relationship("Breed", foreign_keys=[breed_id], lazy="select")
    keyword: Mapped[Keyword] = relationship("Keyword", foreign_keys=[type_id], lazy="select")
    diaries: Mapped[list[Diary]] = relationship("Diary", back_populates="pet", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Pet id={self.id} name={self.name!r} user_id={self.user_id}>"
