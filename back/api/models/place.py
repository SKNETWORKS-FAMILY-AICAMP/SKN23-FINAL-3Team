# -*- coding: utf-8 -*-
"""
models/place.py
---------------
places 테이블 ORM 모델.

반려견 동반 가능 장소 마스터 데이터 (VectorDB 및 DB 검색용).
"""

from __future__ import annotations

from decimal import Decimal
from datetime import datetime
from core.database import Base
from core.type.place import YNEnum, FeeType
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, Numeric, String, Text, UniqueConstraint, Index, func, Enum as SAEnum


class Place(Base):
    """반려견 동반 가능 장소 데이터."""

    __tablename__ = "places"
    __table_args__ = (
        UniqueConstraint("content_id", name="uq_places_content_id"),
        Index("idx_places_type", "content_type_id"),
        Index("idx_places_location", "latitude", "longitude"),
        {
            "comment": "반려견 동반 가능 장소",
            "mysql_engine": "InnoDB",
            "mysql_charset": "utf8mb4",
            "mysql_collate": "utf8mb4_unicode_ci",
        },
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True, comment="장소 PK")
    content_id: Mapped[str] = mapped_column(String(20), nullable=False, comment="한국관광공사 콘텐츠 ID (UNIQUE KEY)")
    content_type_id: Mapped[str] = mapped_column(String(5), nullable=False, comment="관광타입 코드 (12:관광지 14:문화시설 28:레포츠 32:숙박 38:쇼핑 39:음식점)")
    name: Mapped[str] = mapped_column(String(200), nullable=False, comment="장소명")
    address: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="주소")
    tel: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="전화번호")
    
    # Decimal type for latitude/longitude
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True, comment="위도 (GPS Y좌표 / WGS84)")
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True, comment="경도 (GPS X좌표 / WGS84)")
    
    is_indoor: Mapped[bool | None] = mapped_column(TINYINT(1), nullable=True, comment="실내 여부 (NULL=미확인)")
    is_outdoor: Mapped[bool | None] = mapped_column(TINYINT(1), nullable=True, comment="실외 여부 (NULL=미확인)")

    sub_category: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="원본 세부 카테고리 (카페/박물관/동물병원 등)")
    pet_zone_type: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="반려동물 동반 가능 구역 유형 (실내구역/실외구역/전구역)")
    pet_size_limit: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="입장 가능 반려동물 크기/종류")
    pet_restrictions: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="반려동물 동반 시 제한사항")
    has_parking: Mapped[YNEnum | None] = mapped_column(SAEnum(YNEnum), nullable=True, comment="주차 가능 여부 (Y/N)")
    operation_info: Mapped[str | None] = mapped_column(Text, nullable=True, comment="운영시간 및 휴무일 정보")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="장소 통합 설명 텍스트 (VectorDB ChromaDB 임베딩 소스)")

    # ── fee 정규화 (description 자연어 → 정규식/LLM 추출) ─────────────────
    entrance_fee_amount: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="입장료(원). NULL=불명/변동/조건부"
    )
    entrance_fee_type: Mapped[FeeType] = mapped_column(
        SAEnum(FeeType), nullable=False, server_default=FeeType.unknown.value,
        comment="입장료 정규화 타입 (free/fixed/variable/conditional/unknown)",
    )
    extra_fee_amount: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="강아지 추가요금(원). NULL=불명/변동/조건부"
    )
    extra_fee_type: Mapped[FeeType] = mapped_column(
        SAEnum(FeeType), nullable=False, server_default=FeeType.unknown.value,
        comment="추가요금 정규화 타입",
    )

    modified_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="한국관광공사 원본 데이터 최종 수정일")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, server_default=func.now(), comment="수집 등록 일시"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now(), comment="수집 갱신 일시"
    )

    def __repr__(self) -> str:
        return f"<Place id={self.id} content_id={self.content_id!r} name={self.name!r}>"
