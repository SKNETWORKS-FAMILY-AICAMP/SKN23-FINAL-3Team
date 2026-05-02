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

from datetime import date, datetime
from core.database import Base
from core.utils import kst_now
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import (BigInteger, Date, DateTime, ForeignKey, Index, String, Text, func)


def _kst_today() -> date:
    """KST 기준 오늘 날짜를 반환합니다 (`diary_date` default)."""
    return kst_now().date()


class Diary(Base):
    """반려견 동반 기록 다이어리."""

    __tablename__ = "diaries"
    __table_args__ = (
        Index("idx_diaries_user_id", "user_id", "deleted_at"),
        Index("idx_diaries_pet_id", "pet_id"),
        Index("idx_diaries_user_date", "user_id", "diary_date", "deleted_at"),
        Index("idx_diaries_user_favorite", "user_id", "is_favorite", "deleted_at"),
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

    # ── 캘린더·즐겨찾기 ─────────────────────────────────────────────────────
    # diary_date: 일기가 가리키는 날짜. 현 단계는 작성 시점의 KST 날짜를 자동 입력
    # (서비스 create_diary 에서 채움). 추후 사용자가 화면에서 직접 선택 가능.
    diary_date: Mapped[date] = mapped_column(
        Date, nullable=False, default=_kst_today,
        comment="일기 날짜 YYYY-MM-DD (현재 KST 자동 입력, 추후 사용자 선택 가능)",
    )
    # is_favorite: 즐겨찾기 플래그. "하루 1개" 제약은 service.toggle_favorite_diary
    # 의 atomic SWAP 로 보장 (DB UNIQUE 제약 없음).
    is_favorite: Mapped[bool] = mapped_column(
        TINYINT(1), nullable=False, default=False, server_default="0",
        comment="즐겨찾기 여부 (0/1). 하루 1개 제약은 application-level SWAP.",
    )

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
