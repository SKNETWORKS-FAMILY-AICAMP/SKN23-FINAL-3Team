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

from core.type.place import YNEnum


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
    acmpy_type_cd: Optional[str] = Field(None, description="동반유형")
    acmpy_psbl_cpam: Optional[str] = Field(None, description="동반가능동물 설명")
    acmpy_need_mtr: Optional[str] = Field(None, description="동반 시 필요사항")
    rela_poses_fclty: Optional[YNEnum] = Field(None, description="반려동물 관련 구비 시설 여부")
    etc_acmpy_info: Optional[str] = Field(None, description="기타 동반 정보")
    description: Optional[str] = Field(None, description="장소 통합 설명 텍스트")
    modified_time: Optional[datetime] = Field(None, description="한국관광공사 원본 데이터 최종 수정일")
    created_at: datetime = Field(..., description="수집 등록 일시")
    updated_at: datetime = Field(..., description="수집 갱신 일시")
