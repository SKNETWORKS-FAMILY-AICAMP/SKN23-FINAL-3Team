# -*- coding: utf-8 -*-
"""
models/favorite_place.py
------------------------
favorite_places 테이블 ORM 모델.

사용자별 즐겨찾기 장소 (N:M).
- 한 사용자가 여러 장소를 즐겨찾기 가능
- 한 장소를 여러 사용자가 즐겨찾기 가능
- UNIQUE (user_id, place_id) 로 중복 차단 (DB 레벨)
- soft delete 미적용 — 해제는 hard delete

다이어리 즐겨찾기와의 정책 차이는 [[feature-favorites-place]] §책임 분리 참고.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.utils import kst_now


class FavoritePlace(Base):
    """사용자별 즐겨찾기 장소 매핑."""

    __tablename__ = "favorite_places"
    __table_args__ = (
        UniqueConstraint("user_id", "place_id", name="uq_favorite_places_user_place"),
        Index("idx_favorite_places_user", "user_id", "created_at"),
        {
            "comment": "사용자별 즐겨찾기 장소 (N:M, places 공통 풀 공유)",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, comment="즐겨찾기 PK"
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        comment="사용자 ID",
    )
    place_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("places.id", onupdate="CASCADE", ondelete="CASCADE"),
        nullable=False,
        comment="장소 ID (places.id, 내부 BIGINT FK)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=kst_now,
        server_default=func.now(),
        comment="즐겨찾기 등록 시각 (favorited_at 의미)",
    )

    def __repr__(self) -> str:
        return (
            f"<FavoritePlace id={self.id} user_id={self.user_id} "
            f"place_id={self.place_id}>"
        )
