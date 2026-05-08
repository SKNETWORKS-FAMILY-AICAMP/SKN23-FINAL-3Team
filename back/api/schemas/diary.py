# -*- coding: utf-8 -*-
"""
schemas/diary.py
----------------
다이어리 도메인 Pydantic v2 스키마.

- DiaryCreate  : 다이어리 생성 요청 (6하원칙 텍스트, 전부 optional)
- DiaryUpdate  : 수정 요청 (image_id 바인딩 포함, 모든 필드 optional)
- DiaryResponse: 응답 스키마

[2-phase 저장]
 1단계: AI 파이프라인 완료 전 → image_id 없이 먼저 생성 (DiaryCreate)
 2단계: AI 이미지 완성 후   → image_id를 PATCH로 바인딩 (DiaryUpdate)
"""

from __future__ import annotations

# `date` 는 흔히 필드명으로도 사용되어 (예: FavoriteCalendarItem.date) Pydantic v2
# 가 클래스 namespace 에서 type annotation 을 해석할 때 충돌을 일으킨다.
# alias 로 import 해서 필드명/타입명 충돌을 원천 차단한다.
from datetime import date as _Date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from utils.validation import clean_text


# 다이어리 본문(content)은 정책상 상한 없음 — DB TEXT 컬럼 안전 영역으로 보수적 cap.
_DIARY_CONTENT_MAX = 50000
# 6하원칙 슬롯 길이 cap (정책 = 0~1000자, NULL 허용. 자유채팅 다이어리에서 _conversation 텍스트가
# what_text 에 박히는 흐름 정합 — diary_response_service.py:619)
_DIARY_6W_MAX = 1000
# 다이어리 제목 (정책 = 1~50자)
_DIARY_TITLE_MIN = 1
_DIARY_TITLE_MAX = 50


class DiaryCreate(BaseModel):
    """
        다이어리 생성 요청.

        6하원칙 텍스트 및 AI 생성 필드는 모두 optional입니다.
        image_id는 AI 파이프라인 완료 후 PATCH로 바인딩합니다.
    """

    pet_id: int = Field(..., gt=0, description="반려견 ID (pets 테이블 참조)")

    # 6하원칙 (정책 = 0~1000자, NULL 허용. 욕설 검사는 service 단)
    when_text: str | None = Field(None, description="언제 (0~1000자)")
    where_text: str | None = Field(None, description="어디서 (0~1000자)")
    who_text: str | None = Field(None, description="누구와 (0~1000자)")
    what_text: str | None = Field(None, description="무엇을 (0~1000자)")
    how_text: str | None = Field(None, description="어떻게 (0~1000자)")
    why_text: str | None = Field(None, description="왜 (0~1000자)")

    # AI 생성 필드 (선택). title 은 None 허용(AI 자동 생성), 값 들어오면 1~50자.
    title: str | None = Field(None, description="제목 (1~50자, 미입력 시 AI 자동 생성)")
    content: str | None = Field(None, description="본문 (입력 시 빈 문자열 거부)")
    summary: str | None = Field(None, max_length=300, description="AI 생성 요약문")
    emotion: str | None = Field(None, max_length=10, description="감정 이모지")
    image_id: int | None = Field(None, gt=0, description="AI 이미지 ID (생성 완료 후 입력)")

    # 캘린더 키 (현 단계는 미입력 시 서비스에서 KST 오늘 자동 입력)
    diary_date: _Date | None = Field(
        None,
        description="일기 날짜 YYYY-MM-DD. 미입력 시 작성 시점의 KST 날짜로 자동 입력.",
    )

    @field_validator(
        "when_text", "where_text", "who_text", "what_text", "how_text", "why_text",
        mode="before",
    )
    @classmethod
    def _clean_6w(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=0, max_length=_DIARY_6W_MAX, label="6하원칙 슬롯", allow_blank=True)

    @field_validator("title", mode="before")
    @classmethod
    def _clean_title(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=_DIARY_TITLE_MIN, max_length=_DIARY_TITLE_MAX, label="다이어리 제목")

    @field_validator("content", mode="before")
    @classmethod
    def _clean_content(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=1, max_length=_DIARY_CONTENT_MAX, label="다이어리 본문")


class DiaryUpdate(BaseModel):
    """
        다이어리 수정 요청 (PATCH 시맨틱).

        제공된 필드만 업데이트합니다.
        image_id 바인딩 시 images 테이블 참조 무결성을 검증합니다.
    """

    pet_id: int | None = Field(None, gt=0, description="반려견 ID")

    # 6하원칙 (정책 = 0~1000자, NULL 허용)
    when_text: str | None = Field(None, description="언제 (0~1000자)")
    where_text: str | None = Field(None, description="어디서 (0~1000자)")
    who_text: str | None = Field(None, description="누구와 (0~1000자)")
    what_text: str | None = Field(None, description="무엇을 (0~1000자)")
    how_text: str | None = Field(None, description="어떻게 (0~1000자)")
    why_text: str | None = Field(None, description="왜 (0~1000자)")

    # AI 생성 필드 + 이미지 바인딩
    title: str | None = Field(None, description="제목 (1~50자)")
    content: str | None = Field(None, description="본문 (입력 시 빈 문자열 거부)")
    summary: str | None = Field(None, max_length=300)
    emotion: str | None = Field(None, max_length=10)
    image_id: int | None = Field(None, gt=0, description="AI 이미지 ID 바인딩")

    # 캘린더 키 (사용자 수정 가능 — 추후 UI 도입 시 사용)
    diary_date: _Date | None = Field(None, description="일기 날짜 YYYY-MM-DD")

    @field_validator(
        "when_text", "where_text", "who_text", "what_text", "how_text", "why_text",
        mode="before",
    )
    @classmethod
    def _clean_6w(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=0, max_length=_DIARY_6W_MAX, label="6하원칙 슬롯", allow_blank=True)

    @field_validator("title", mode="before")
    @classmethod
    def _clean_title(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=_DIARY_TITLE_MIN, max_length=_DIARY_TITLE_MAX, label="다이어리 제목")

    @field_validator("content", mode="before")
    @classmethod
    def _clean_content(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=1, max_length=_DIARY_CONTENT_MAX, label="다이어리 본문")


class DiaryResponse(BaseModel):
    """다이어리 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="일기 ID")
    user_id: int = Field(..., description="사용자 ID")
    pet_id: int = Field(..., description="반려견 ID")
    image_id: int | None = Field(None, description="AI 이미지 ID")

    # 6하원칙
    when_text: str | None = None
    where_text: str | None = None
    who_text: str | None = None
    what_text: str | None = None
    how_text: str | None = None
    why_text: str | None = None

    # AI 생성 필드
    title: str | None = None
    content: str | None = None
    summary: str | None = None
    emotion: str | None = None

    # 캘린더·즐겨찾기
    diary_date: _Date = Field(..., description="일기 날짜 YYYY-MM-DD")
    is_favorite: bool = Field(False, description="즐겨찾기 여부")

    created_at: datetime = Field(..., description="작성 일시")
    updated_at: datetime = Field(..., description="수정 일시")


class FavoriteCalendarItem(BaseModel):
    """캘린더 셀에 들어갈 즐겨찾기 일기 1건의 경량 페이로드."""

    date: _Date = Field(..., description="일기 날짜 YYYY-MM-DD")
    diary_id: int = Field(..., description="다이어리 ID (셀 클릭 시 상세 라우팅)")
    emotion: str = Field("", description="감정 이모지 (캘린더 셀 표시용)")


class FavoriteCalendarResponse(BaseModel):
    """캘린더 화면에서 한 달치 즐겨찾기 일기를 한 번에 받는 응답 스키마."""

    year: int = Field(..., ge=1900, le=2100, description="조회 연도")
    month: int = Field(..., ge=1, le=12, description="조회 월 (1-12)")
    items: list[FavoriteCalendarItem] = Field(
        ..., description="해당 월의 즐겨찾기 일기 목록 (diary_date ASC)"
    )
