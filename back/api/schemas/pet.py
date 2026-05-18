# -*- coding: utf-8 -*-
"""
schemas/pet.py
--------------
반려견 도메인 Pydantic v2 스키마.

- PetCreate  : 반려견 등록 요청
- PetUpdate  : 정보 수정 요청 (PATCH, 모든 필드 optional)
- PetResponse: 응답 스키마
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from services.common_service import calculate_age

from core.type.gender import PetGenderEnum
from utils.validation import clean_text, validate_pet_birth


class _Image(BaseModel):
    """이미지 URL 로딩용 내부 스키마."""
    model_config = ConfigDict(from_attributes=True)
    file_url: str


class PetCreate(BaseModel):
    """반려견 등록 요청."""

    breed_id: int = Field(..., gt=0, description="견종 ID (breeds 테이블 참조)")
    name: str = Field(..., description="반려견 이름 (1~20자, trim 후. 욕설 검사는 service 단)")
    birth_date: date | None = Field(None, description="생년월일 (오늘-30년 ~ 오늘)")
    gender: PetGenderEnum | None = Field(None, description="성별")
    is_neutered: bool | None = Field(None, description="중성화 여부 (미입력 가능)")
    selected_tags: list[Any] | None = Field(None, description="선택한 성격 태그 목록 (JSON). type_id 는 백엔드가 자동 계산.")
    image_id: int | None = Field(None, gt=0, description="프로필 이미지 ID (images.id 참조, 등록 시 선택)")

    @field_validator("name", mode="before")
    @classmethod
    def _clean_name(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=1, max_length=20, label="반려견 이름")

    @field_validator("birth_date", mode="after")
    @classmethod
    def _check_pet_birth(cls, v: date | None) -> date | None:
        return validate_pet_birth(v)


class PetUpdate(BaseModel):
    """
        반려견 정보 수정 요청.

        제공된 필드만 업데이트합니다 (PATCH 시맨틱).
    """

    breed_id: int | None = Field(None, gt=0, description="견종 ID")
    name: str | None = Field(None, description="반려견 이름 (1~20자, trim 후. 욕설 검사는 service 단)")
    birth_date: date | None = Field(None, description="생년월일 (오늘-30년 ~ 오늘)")
    gender: PetGenderEnum | None = Field(None, description="성별")
    is_neutered: bool | None = Field(None, description="중성화 여부")
    selected_tags: list[Any] | None = Field(None, description="성격 태그 목록. type_id 는 백엔드가 자동 재계산.")
    image_id: int | None = Field(None, gt=0, description="프로필 이미지 ID (images.id 참조)")

    @field_validator("name", mode="before")
    @classmethod
    def _clean_name(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=1, max_length=20, label="반려견 이름")

    @field_validator("birth_date", mode="after")
    @classmethod
    def _check_pet_birth(cls, v: date | None) -> date | None:
        return validate_pet_birth(v)


class _Breed(BaseModel):
    """견종 이름 로딩용 내부 스키마."""
    model_config = ConfigDict(from_attributes=True)
    name_ko: str


class _PetProfile(BaseModel):
    """프로필 분석 결과 내부 스키마."""
    model_config = ConfigDict(from_attributes=True)
    profile_json: dict
    analyzed_at: datetime
    image_id: int | None = None


class PetResponse(BaseModel):
    """반려견 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="반려견 ID")
    user_id: int = Field(..., description="보호자 사용자 ID")
    breed_id: int = Field(..., description="견종 ID")
    name: str = Field(..., description="반려견 이름")
    birth_date: date | None = Field(None, description="생년월일")
    gender: PetGenderEnum | None = Field(None, description="성별")
    is_neutered: bool | None = Field(None, description="중성화 여부")
    type_id: int | None = Field(None, description="대표 성격 키워드 ID")
    type_name: str | None = Field(
        None,
        description="성향 타입 한글 표시명 (keywords.name). Pet ORM property 매핑.",
    )
    selected_tags: list[Any] | None = Field(None, description="성격 태그 목록")
    created_at: datetime = Field(..., description="등록 일시")
    updated_at: datetime = Field(..., description="수정 일시")

    # selectin 로드된 관계 — 직렬화에서 제외, computed_field 내부 참조용
    breed: _Breed | None = Field(default=None, exclude=True)
    image: _Image | None = Field(default=None, exclude=True)
    profile: _PetProfile | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def breed_name(self) -> str | None:
        """견종 한국어 이름."""
        return self.breed.name_ko if self.breed else None

    @computed_field
    @property
    def image_url(self) -> str | None:
        return self.image.file_url if self.image else None

    @computed_field
    @property
    def age(self) -> int | None:
        return calculate_age(self.birth_date)

    @computed_field
    @property
    def english_prompt(self) -> str | None:
        """AI 프로필 분석에서 추출한 영문 외형 프롬프트."""
        if self.profile and self.profile.profile_json:
            cs = self.profile.profile_json.get("character_sheet", {})
            return cs.get("english_prompt")
        return None

    @computed_field
    @property
    def must_include_keywords(self) -> list[str] | None:
        """AI 프로필 분석에서 추출한 필수 키워드."""
        if self.profile and self.profile.profile_json:
            cs = self.profile.profile_json.get("character_sheet", {})
            return cs.get("must_include_keywords")
        return None
