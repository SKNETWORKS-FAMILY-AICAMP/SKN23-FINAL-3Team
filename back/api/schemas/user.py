# -*- coding: utf-8 -*-
"""
schemas/user.py
---------------
사용자 도메인 Pydantic v2 스키마.

- UserResponse : 사용자 단건/목록 응답
- UserUpdate   : 프로필 수정 요청 (PATCH, 모든 필드 optional)
"""

from __future__ import annotations

import enum
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field
from services.common_service import calculate_age


class GenderEnum(str, enum.Enum):
    """성별 Enum (API 응답/요청 공용)."""
    MALE = "MALE"
    FEMALE = "FEMALE"


class UserResponse(BaseModel):
    """사용자 단건 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="사용자 ID")
    email: str = Field(..., description="이메일 주소")
    nickname: str = Field(..., description="닉네임")
    gender: GenderEnum | None = Field(None, description="성별")
    birth_date: date | None = Field(None, description="생년월일")
    profile_id: int | None = Field(None, description="프로필 이미지 ID (온보딩 전 NULL)")
    provider: str = Field(..., description="소셜 로그인 제공자 (kakao/google/naver)")
    type_id: int | None = Field(None, description="대표 성향 키워드 ID (온보딩 전 NULL)")
    selected_tags: list[Any] | None = Field(None, description="선택한 여행 성향 태그 목록")
    created_at: datetime = Field(..., description="가입 일시")
    updated_at: datetime = Field(..., description="최종 수정 일시")

    @computed_field
    @property
    def age(self) -> int | None:
        return calculate_age(self.birth_date)


class UserUpdate(BaseModel):
    """
        사용자 프로필 수정 요청 스키마.

        제공된 필드만 업데이트합니다 (PATCH 시맨틱).
        모든 필드는 optional입니다.
    """

    nickname: str | None = Field(
        None,
        min_length=1,
        max_length=50,
        description="닉네임 (1~50자)",
    )
    gender: GenderEnum | None = Field(None, description="성별")
    birth_date: date | None = Field(
        None,
        description="생년월일",
    )
    profile_id: int | None = Field(
        None,
        gt=0,
        description="프로필 이미지 ID (images 테이블 참조)",
    )
    type_id: int | None = Field(
        None,
        gt=0,
        description="대표 성향 키워드 ID (keywords 테이블 참조)",
    )
    selected_tags: list[Any] | None = Field(
        None,
        description="선택한 여행 성향 태그 목록 (JSON 배열)",
    )
