# -*- coding: utf-8 -*-
"""
models/keyword.py
-----------------
keywords 테이블 ORM 모델.

사용자/반려견 성향 태그 마스터 데이터.
users(type_id), pets(type_id) 에서 FK로 참조됩니다.
"""

from __future__ import annotations

from datetime import datetime
from core.utils import kst_now
from core.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, DateTime, String, Text, func



class Keyword(Base):
    """성향 키워드 마스터 데이터."""

    __tablename__ = "keywords"
    __table_args__ = {
        "comment": "키워드 마스터 데이터",
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="키워드 ID",
    )
    category: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        comment="분류 (USER / PET)",
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="키워드명 (화면 노출용)",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="키워드 설명",
    )
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=kst_now,
        server_default=func.now(),
        comment="등록 일시",
    )

    def __repr__(self) -> str:
        return f"<Keyword id={self.id} category={self.category!r} name={self.name!r}>"
