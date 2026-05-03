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
    entrance_fee_type: FeeType = Field(FeeType.unknown, description="입장료 정규화 타입 (free/fixed/variable/conditional/unknown)")
    extra_fee_amount: Optional[int] = Field(None, description="추가요금(원). NULL=불명/변동/조건부")
    extra_fee_type: FeeType = Field(FeeType.unknown, description="추가요금 정규화 타입")
    modified_time: Optional[datetime] = Field(None, description="한국관광공사 원본 데이터 최종 수정일")
    created_at: datetime = Field(..., description="수집 등록 일시")
    updated_at: datetime = Field(..., description="수집 갱신 일시")


class PlaceFavoriteItem(BaseModel):
    """
        즐겨찾기 장소 목록 셀용 경량 페이로드.

        프론트가 이미지·주소 등은 별도 API(GET /api/places/by-name 등) 로
        보강하므로, 본 스키마에는 카드 식별·정렬에 필요한 최소 필드만 포함한다.
    """

    content_id: str = Field(..., description="한국관광공사 콘텐츠 ID (PATCH 호출 시 path param)")
    name: str = Field(..., description="장소명")
    sub_category: str = Field("", description="세부 분류 (카페/공원/숙박 등)")
    favorited_at: datetime = Field(..., description="즐겨찾기 등록 시각")


class PlaceFavoriteResponse(BaseModel):
    """즐겨찾기 장소 목록 응답 스키마."""

    items: list[PlaceFavoriteItem] = Field(
        ..., description="즐겨찾기 장소 목록 (favorited_at DESC)"
    )


class PlaceFavoriteToggleResponse(BaseModel):
    """즐겨찾기 토글 결과 응답 스키마."""

    content_id: str = Field(..., description="대상 장소 콘텐츠 ID")
    is_favorite: bool = Field(..., description="토글 후 상태 (True=즐겨찾기, False=해제)")
    favorited_at: Optional[datetime] = Field(
        None, description="즐겨찾기 등록 시각 (해제 시 None)"
    )
