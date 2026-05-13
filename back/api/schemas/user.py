# -*- coding: utf-8 -*-
"""
schemas/user.py
---------------
사용자 도메인 Pydantic v2 스키마.

- UserResponse : 사용자 단건/목록 응답
- UserUpdate   : 프로필 수정 요청 (PATCH, 모든 필드 optional)
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator
from services.common_service import calculate_age

from core.type.gender import GenderEnum
from schemas.pet import PetResponse
from utils.validation import clean_text, validate_user_birth


class _ProfileImage(BaseModel):
    """프로필 이미지 URL 로딩용 내부 스키마."""
    model_config = ConfigDict(from_attributes=True)
    file_url: str


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
    type_name: str | None = Field(
        None,
        description="성향 타입 한글 표시명 (keywords.name). User ORM property 매핑.",
    )
    primary_pet_id: int | None = Field(None, description="대표 반려견 ID (미설정 시 NULL)")
    primary_pet: PetResponse | None = Field(
        None, description="대표 반려견 풀 페이로드 (마이페이지 카드 표시용)"
    )
    selected_tags: list[Any] | None = Field(None, description="선택한 여행 성향 태그 목록")
    created_at: datetime = Field(..., description="가입 일시")
    updated_at: datetime = Field(..., description="최종 수정 일시")
    terms_agreed_at: datetime | None = Field(
        None,
        description="서비스 이용약관 동의 시점. NULL 이면 /step 재진입 필요.",
    )
    privacy_agreed_at: datetime | None = Field(
        None,
        description="개인정보처리방침 동의 시점. NULL 이면 /step 재진입 필요.",
    )

    # selectin 로드된 관계 — 직렬화에서 제외, computed_field 내부 참조용
    profile: _ProfileImage | None = Field(default=None, exclude=True)

    @computed_field
    @property
    def profile_image_url(self) -> str | None:
        return self.profile.file_url if self.profile else None

    @computed_field
    @property
    def age(self) -> int | None:
        return calculate_age(self.birth_date)


class AgreementsRequest(BaseModel):
    """약관·개인정보처리방침 동의 요청 (POST /users/me/agreements).

    둘 다 true 일 때만 동의 완료 처리. 하나라도 false 면 400.
    """

    terms_agreed: bool = Field(..., description="서비스 이용약관 동의 여부 (true 필수)")
    privacy_agreed: bool = Field(..., description="개인정보처리방침 동의 여부 (true 필수)")


class UserUpdate(BaseModel):
    """
        사용자 프로필 수정 요청 스키마.

        제공된 필드만 업데이트합니다 (PATCH 시맨틱).
        모든 필드는 optional입니다.
    """

    nickname: str | None = Field(
        None,
        description="닉네임 (1~20자, trim 후. 욕설 검사는 service 단)",
    )
    gender: GenderEnum | None = Field(None, description="성별")
    birth_date: date | None = Field(
        None,
        description="생년월일 (1900-01-01 ~ 오늘-14년, 개인정보보호법 만 14세 이상)",
    )

    @field_validator("nickname", mode="before")
    @classmethod
    def _clean_nickname(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=1, max_length=20, label="닉네임")

    @field_validator("birth_date", mode="after")
    @classmethod
    def _check_user_birth(cls, v: date | None) -> date | None:
        return validate_user_birth(v)
    profile_id: int | None = Field(
        None,
        gt=0,
        description="프로필 이미지 ID (images 테이블 참조)",
    )
    primary_pet_id: int | None = Field(
        None,
        gt=0,
        description=(
            "대표 반려견 ID (pets 테이블 참조). 본인 소유의 활성 반려견이어야 함. "
            "명시적으로 null 을 보내 해제하려면 별도 처리 필요(현재는 미지원)."
        ),
    )
    selected_tags: list[Any] | None = Field(
        None,
        description="선택한 여행 성향 태그 목록 (JSON 배열). type_id 는 백엔드가 자동 재계산.",
    )
