# -*- coding: utf-8 -*-
"""
models/image.py
---------------
images 테이블 ORM 모델.

S3에 업로드된 이미지의 메타데이터를 저장합니다.
users(profile_id), diaries(image_id) 에서 FK로 참조됩니다.
"""

from __future__ import annotations

from datetime import datetime
from core.utils import kst_now

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class Image(Base):
    """이미지 파일 메타데이터 (S3 연동)."""

    __tablename__ = "images"
    __table_args__ = {
        "comment": "이미지 파일 메타데이터 (S3 연동)",
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="이미지 ID",
    )
    file_url: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="AWS S3 파일 URL",
    )
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="원본 파일명",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=kst_now,
        server_default=func.now(),
        comment="생성 일시",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
        comment="삭제 일시",
    )

    def __repr__(self) -> str:
        return f"<Image id={self.id} file_name={self.file_name!r}>"
