# -*- coding: utf-8 -*-
"""
schemas/place.py
----------------
장소 도메인 Pydantic v2 스키마.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from core.type.place import YNEnum, FeeType


class PlaceResponse(BaseModel):
    """장소 데이터 응답."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="장소 PK")
    content_id: str = Field(..., description="한국관광공사 콘텐츠 ID")
    content_type_id: str = Field(..., description="관광타입 코드")
    name: str = Field(..., description="장소명")
    address: Optional[str] = Field(None, description="주소")
    tel: Optional[str] = Field(None, description="전화번호")
    latitude: Optional[Decimal] = Field(None, description="위도")
    longitude: Optional[Decimal] = Field(None, description="경도")
    firstimage: Optional[str] = Field(None, description="대표 이미지 원본 URL")
    firstimage2: Optional[str] = Field(None, description="대표 이미지 썸네일 URL")
    is_indoor: Optional[bool] = Field(None, description="실내 여부")
    is_outdoor: Optional[bool] = Field(None, description="실외 여부")
    sub_category: Optional[str] = Field(None, description="원본 세부 카테고리")
    pet_zone_type: Optional[str] = Field(None, description="반려동물 동반 가능 구역 유형 (실내구역/실외구역/전구역)")
    pet_size_limit: Optional[str] = Field(None, description="입장 가능 반려동물 크기/종류")
    pet_restrictions: Optional[str] = Field(None, description="반려동물 동반 시 제한사항")
    has_parking: Optional[YNEnum] = Field(None, description="주차 가능 여부 (Y/N)")
    operation_info: Optional[str] = Field(None, description="운영시간 및 휴무일 정보")
    description: Optional[str] = Field(None, description="장소 통합 설명 텍스트")
    entrance_fee_amount: Optional[int] = Field(None, description="입장료(원). NULL=불명/변동/조건부")
    entrance_fee_type: FeeType = Field(FeeType.UNKNOWN, description="입장료 정규화 타입 (free/fixed/variable/conditional/unknown)")
    extra_fee_amount: Optional[int] = Field(None, description="추가요금(원). NULL=불명/변동/조건부")
    extra_fee_type: FeeType = Field(FeeType.UNKNOWN, description="추가요금 정규화 타입")
    modified_time: Optional[datetime] = Field(None, description="한국관광공사 원본 데이터 최종 수정일")
    created_at: datetime = Field(..., description="수집 등록 일시")
    updated_at: datetime = Field(..., description="수집 갱신 일시")
