# -*- coding: utf-8 -*-
"""
models/pet.py
-------------
pets 테이블 ORM 모델.

반려견 기본 정보.
- user_id  : users.id FK
- breed_id : breeds.id FK
- type_id  : keywords.id FK (대표 성격 키워드)
- Soft Delete: deleted_at 기록
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from datetime import datetime
from core.utils import kst_now
from core.database import Base
from core.type.gender import PetGenderEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (BigInteger, Boolean, Date, DateTime, Enum as SAEnum, ForeignKey, Index, JSON, String, func)

if TYPE_CHECKING:
    from models.image import Image


class Pet(Base):
    """반려견 기본 정보."""

    __tablename__ = "pets"
    __table_args__ = (
        Index("idx_pets_user_id", "user_id"),
        {
            "comment": "반려견 기본 정보",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="반려견 ID")

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

    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="반려견 이름")
    birth_date: Mapped[datetime | None] = mapped_column(Date, nullable=True, comment="생년월일")
    gender: Mapped[PetGenderEnum] = mapped_column(SAEnum(PetGenderEnum), nullable=False, comment="성별")
    is_neutered: Mapped[bool | None] = mapped_column(Boolean, nullable=True, comment="중성화 여부 (NULL=미입력)")

    # FK → keywords
    type_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("keywords.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
        comment="대표 성격 키워드 ID",
    )

    selected_tags: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True, comment="선택한 성격 태그 목록")

    # FK → images (반려견 이미지)
    image_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("images.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True,
        comment="프로필 이미지 ID (images.id FK)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, server_default=func.now(),
        comment="등록 일시",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, onupdate=kst_now, server_default=func.now(),
        comment="수정 일시",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="삭제 일시")

    # ── Relationships ──────────────────────────────────────────────────────
    # users.primary_pet_id ↔ pets.user_id 양방향 FK 라 foreign_keys 명시 필수.
    user: Mapped[User] = relationship(
        "User",
        back_populates="pets",
        foreign_keys=[user_id],
    )
    breed: Mapped[Breed] = relationship("Breed", foreign_keys=[breed_id], lazy="selectin")
    # selectin: PetResponse.type_name property 가 동기 access 안전하도록 prefetch.
    type: Mapped[Keyword | None] = relationship("Keyword", foreign_keys=[type_id], lazy="selectin")
    image: Mapped[Image | None] = relationship("Image", foreign_keys=[image_id], lazy="selectin")
    profile = relationship("PetProfile", back_populates="pet", uselist=False, lazy="selectin")
    diaries: Mapped[list[Diary]] = relationship("Diary", back_populates="pet", cascade="all, delete-orphan")

    @property
    def type_name(self) -> str | None:
        """PetResponse 의 from_attributes 매핑용 — keywords.name 동적 추출.

        Pet.type relationship 이 lazy=selectin 으로 prefetch 되어 동기 access 안전.
        type_id 가 NULL 이면 None 반환 — 마이페이지에서 "성향 미설정" 표시 분기.
        """
        return self.type.name if self.type else None

    def __repr__(self) -> str:
        return f"<Pet id={self.id} name={self.name!r} user_id={self.user_id}>"
