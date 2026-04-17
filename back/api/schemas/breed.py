# -*- coding: utf-8 -*-
"""
schemas/breed.py
----------------
견종 도메인 Pydantic v2 스키마.

BreedResponse: 견종 단건/목록 응답 스키마
"""

from __future__ import annotations

from datetime import datetime

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BreedSizeEnum(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"

class ActivityLevelEnum(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class BreedResponse(BaseModel):
    """견종 단건 응답."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="견종 ID")
    name_ko: str = Field(..., description="견종명 (한국어)")
    name_en: str = Field(..., description="견종명 (영어)")
    top10: bool = Field(..., description="인기 TOP10 여부")
    size: Optional[BreedSizeEnum] = Field(None, description="견종 크기 분류")
    activity_level: Optional[ActivityLevelEnum] = Field(None, description="활동량 수준")
    temperament: Optional[str] = Field(None, description="성격 태그")
    breed_group: Optional[str] = Field(None, description="견종 그룹")
    image_url: Optional[str] = Field(None, description="견종 대표 이미지 URL")
    created_at: datetime = Field(..., description="등록 일시")
