# -*- coding: utf-8 -*-
"""
models/pet_profile.py
---------------------
pet_profiles 테이블 ORM 모델.

GPT-4o Vision 으로 반려견 사진을 분석한 구조화된 외형 JSON 저장.
pets 와 1:1 관계 (pet_id UNIQUE).
"""

from __future__ import annotations

from datetime import datetime

from core.database import Base
from core.utils import kst_now
from sqlalchemy import BigInteger, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship


class PetProfile(Base):
    """반려견 AI 프로필 분석 결과."""

    __tablename__ = "pet_profiles"
    __table_args__ = (
        {
            "comment": "반려견 AI 프로필 분석 결과",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="PK",
    )

    pet_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pets.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        comment="pets.id FK (1:1)",
    )

    image_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("images.id", onupdate="CASCADE", ondelete="SET NULL"),
        nullable=True,
        comment="분석에 사용된 이미지 ID",
    )

    profile_json: Mapped[dict] = mapped_column(
        JSON, nullable=False, comment="GPT-4o Vision 분석 결과 전체 JSON",
    )

    analyzed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, server_default=func.now(),
        comment="분석 일시",
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

    # ── Relationships ──
    pet = relationship("Pet", back_populates="profile", foreign_keys=[pet_id])
    image = relationship("Image", foreign_keys=[image_id], lazy="selectin")

    def __repr__(self) -> str:
        return f"<PetProfile id={self.id} pet_id={self.pet_id}>"
