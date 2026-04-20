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
from core.utils import kst_now

from sqlalchemy import BigInteger, Boolean, DateTime, String, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.type.breed import ActivityLevelEnum, BreedSizeEnum


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
    size: Mapped[BreedSizeEnum | None] = mapped_column(
        SAEnum(BreedSizeEnum),
        nullable=True,
        comment="견종 크기 분류 (소형:<10kg, 중형:10~25kg, 대형:>25kg)",
    )
    activity_level: Mapped[ActivityLevelEnum | None] = mapped_column(
        SAEnum(ActivityLevelEnum),
        nullable=True,
        comment="활동량 수준 (추천 점수 계산 활용)",
    )
    temperament: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="성격 태그 문자열 (쉼표 구분, 영문 원본)",
    )
    breed_group: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="견종 그룹 (Toy/Sporting/Herding/Hound 등)",
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="견종 대표 이미지 URL (Dog CEO API 캐싱)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=kst_now,
        server_default=func.now(),
        comment="등록 일시",
    )

    def __repr__(self) -> str:
        return f"<Breed id={self.id} name_ko={self.name_ko!r}>"
