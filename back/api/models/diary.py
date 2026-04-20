# -*- coding: utf-8 -*-
"""
models/diary.py
---------------
diaries 테이블 ORM 모델.

반려견 동반 기록 다이어리 (6하원칙 구조).
- user_id : users.id FK
- pet_id  : pets.id FK
- image_id: images.id FK (AI 생성 이미지, nullable → 2-phase 저장 지원)

⚠️ DDL 원본은 image_id NOT NULL이나, AI 파이프라인 지연으로 인한
   2-phase 저장(생성 → 이미지 완성 후 PATCH 바인딩)을 위해 nullable로 변경합니다.
"""

from __future__ import annotations

from datetime import datetime
from core.database import Base
from core.utils import kst_now
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (BigInteger, DateTime, ForeignKey, Index, String, Text, func)


class Diary(Base):
    """반려견 동반 기록 다이어리."""

    __tablename__ = "diaries"
    __table_args__ = (
        Index("idx_diaries_user_id", "user_id", "deleted_at"),
        Index("idx_diaries_pet_id", "pet_id"),
        {
            "comment": "반려견 동반 기록 다이어리 (6하원칙 구조)",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="일기 ID")

    # FK → users
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False, comment="사용자 ID",
    )
    # FK → pets
    pet_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("pets.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False, comment="반려견 ID",
    )
    # FK → images (nullable: 2-phase 저장 지원)
    image_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("images.id", onupdate="CASCADE", ondelete="RESTRICT"),
        nullable=True, comment="AI 이미지 ID (AI 완성 후 PATCH로 바인딩)",
    )

    # ── 6하원칙 필드 ────────────────────────────────────────────────────────
    when_text: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="언제")
    where_text: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="어디서")
    who_text: Mapped[str | None] = mapped_column(String(255), nullable=True, comment="누구와")
    what_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="무엇을")
    how_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="어떻게")
    why_text: Mapped[str | None] = mapped_column(Text, nullable=True, comment="왜")

    # ── AI 생성 필드 ────────────────────────────────────────────────────────
    title: Mapped[str | None] = mapped_column(String(200), nullable=True, comment="제목 (AI 자동 생성)")
    content: Mapped[str | None] = mapped_column(Text, nullable=True, comment="본문 (AI 자동 작성)")
    summary: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="AI 생성 요약문")
    emotion: Mapped[str | None] = mapped_column(String(10), nullable=True, comment="감정 이모지")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, server_default=func.now(),
        comment="작성 일시",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False,
        default=kst_now, onupdate=kst_now, server_default=func.now(),
        comment="수정 일시",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, default=None, comment="삭제 일시")

    # ── Relationships ──────────────────────────────────────────────────────
    user: Mapped[User] = relationship("User", back_populates="diaries")
    pet: Mapped[Pet] = relationship("Pet", back_populates="diaries")
    image: Mapped[Image | None] = relationship("Image", foreign_keys=[image_id], lazy="select")

    def __repr__(self) -> str:
        return f"<Diary id={self.id} user_id={self.user_id} pet_id={self.pet_id}>"
