# -*- coding: utf-8 -*-
"""
models/breed.py
---------------
breeds 테이블 ORM 모델.

견종 마스터 데이터. pets(breed_id) 에서 FK로 참조됩니다.
초기 데이터는 db/seeds/breeds_seed.py 로 적재합니다.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Breed(Base):
    """견종 마스터 데이터."""

    __tablename__ = "breeds"
    __table_args__ = {
        "comment": "견종 마스터 데이터",
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="견종 ID",
    )
    name_ko: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="견종명 (한국어)",
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="견종명 (영어)",
    )
    top10: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="인기 견종 TOP10 여부 (화면 노출)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        server_default=func.now(),
        comment="등록 일시",
    )

    def __repr__(self) -> str:
        return f"<Breed id={self.id} name_ko={self.name_ko!r}>"
