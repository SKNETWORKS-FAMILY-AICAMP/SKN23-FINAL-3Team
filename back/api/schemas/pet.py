# -*- coding: utf-8 -*-
"""
schemas/pet.py
--------------
반려동물 도메인 Pydantic v2 스키마.

- PetCreate  : 반려동물 등록 요청
- PetUpdate  : 정보 수정 요청 (PATCH, 모든 필드 optional)
- PetResponse: 응답 스키마
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field
from services.common_service import calculate_age


class PetGenderEnum(str, enum.Enum):
    """반려동물 성별."""
    MALE = "MALE"
    FEMALE = "FEMALE"


class PetCreate(BaseModel):
    """반려동물 등록 요청."""

    breed_id: int = Field(..., gt=0, description="견종 ID (breeds 테이블 참조)")
    name: str = Field(..., min_length=1, max_length=50, description="반려동물 이름")
    birth_date: date | None = Field(None, description="생년월일 (YYYY-MM-DD)")
    gender: PetGenderEnum | None = Field(None, description="성별")
    is_neutered: bool | None = Field(None, description="중성화 여부 (미입력 가능)")
    type_id: int | None = Field(None, gt=0, description="대표 성격 키워드 ID (keywords 테이블 참조)")
    selected_tags: list[Any] | None = Field(None, description="선택한 성격 태그 목록 (JSON)")


class PetUpdate(BaseModel):
    """
        반려동물 정보 수정 요청.

        제공된 필드만 업데이트합니다 (PATCH 시맨틱).
    """

    breed_id: int | None = Field(None, gt=0, description="견종 ID")
    name: str | None = Field(None, min_length=1, max_length=50, description="이름")
    birth_date: date | None = Field(None, description="생년월일")
    gender: PetGenderEnum | None = Field(None, description="성별")
    is_neutered: bool | None = Field(None, description="중성화 여부")
    type_id: int | None = Field(None, gt=0, description="대표 성격 키워드 ID")
    selected_tags: list[Any] | None = Field(None, description="성격 태그 목록")


class PetResponse(BaseModel):
    """반려동물 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="반려동물 ID")
    user_id: int = Field(..., description="보호자 사용자 ID")
    breed_id: int = Field(..., description="견종 ID")
    name: str = Field(..., description="반려동물 이름")
    birth_date: date | None = Field(None, description="생년월일")
    gender: PetGenderEnum | None = Field(None, description="성별")
    is_neutered: bool | None = Field(None, description="중성화 여부")
    type_id: int | None = Field(None, description="대표 성격 키워드 ID")
    selected_tags: list[Any] | None = Field(None, description="성격 태그 목록")
    created_at: datetime = Field(..., description="등록 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    @computed_field
    @property
    def age(self) -> int | None:
        return calculate_age(self.birth_date)
