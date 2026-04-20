# -*- coding: utf-8 -*-
"""
models/place.py
---------------
places 테이블 ORM 모델.

반려견 동반 가능 장소 마스터 데이터 (VectorDB 및 DB 검색용).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, Boolean, DateTime, Numeric, String, Text, UniqueConstraint, Index, func, Enum as SAEnum
from sqlalchemy.dialects.mysql import TINYINT
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from core.type.place import YNEnum


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
    
    firstimage: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="대표 이미지 원본 URL (약 500x333, 상세 화면용)")
    firstimage2: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="대표 이미지 썸네일 URL (약 150x100, 목록 화면용)")
    
    is_indoor: Mapped[bool | None] = mapped_column(TINYINT(1), nullable=True, comment="실내 여부 (NULL=미확인)")
    
    acmpy_type_cd: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="동반유형 (예: 전구역 동반가능 / 일부구역 동반가능)")
    acmpy_psbl_cpam: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="동반가능동물 설명 (예: 전 견종 가능, 맹견 입마개 필수)")
    acmpy_need_mtr: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="동반 시 필요사항 (예: 목줄 착용)")
    rela_poses_fclty: Mapped[YNEnum | None] = mapped_column(SAEnum(YNEnum), nullable=True, comment="반려동물 관련 구비 시설 (Y/N)")
    etc_acmpy_info: Mapped[str | None] = mapped_column(Text, nullable=True, comment="기타 동반 정보 (상세 안내 텍스트)")
    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment="장소 통합 설명 텍스트 (VectorDB ChromaDB 임베딩 소스)")
    
    modified_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="한국관광공사 원본 데이터 최종 수정일")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, server_default=func.now(), comment="수집 등록 일시"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=func.now(), comment="수집 갱신 일시"
    )

    def __repr__(self) -> str:
        return f"<Place id={self.id} content_id={self.content_id!r} name={self.name!r}>"
