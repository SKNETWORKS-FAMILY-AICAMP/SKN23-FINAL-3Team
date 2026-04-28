# -*- coding: utf-8 -*-
"""
schemas/chat_message.py
-----------------------
채팅 메시지 도메인 Pydantic v2 스키마.

- MessageCreate  : 메시지 저장 요청
- MessageResponse: 응답 스키마
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class MessageCreate(BaseModel):
    """
        채팅 메시지 저장 요청.

        role은 LLM 컨텍스트 규격에 맞게 user / assistant / system 중 하나여야 합니다.
    """

    role: Literal["user", "assistant", "system"] = Field(
        ...,
        description="발신자 구분 (user | assistant | system)",
    )
    content: str = Field(..., min_length=1, description="메시지 본문")
    pet_id: int | None = Field(default=None, description="현재 선택한 반려견 ID")


class MessageResponse(BaseModel):
    """채팅 메시지 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="메시지 ID")
    room_id: int = Field(..., description="채팅방 ID")
    role: str = Field(..., description="발신자 구분 (user | assistant | system)")
    content: str = Field(..., description="메시지 본문")
    created_at: datetime = Field(..., description="발송 일시")


class IntentInfo(BaseModel):
    """의도 분류 결과 메타데이터."""

    intent: str = Field(..., description="분류된 의도 레이블 (예: 장소추천, 다이어리 작성, 시설정보)")
    confidence: float = Field(..., description="분류 신뢰도 (0.0~1.0)")


class FacilityCard(BaseModel):
    """
        시설정보 의도 응답에 첨부되는 단일 시설 카드 페이로드.

        프론트가 이 데이터로 챗방 우측 패널의 시설 상세 카드와 지도 단일 좌표 포커스를 그린다.
    """

    name: str = Field(..., description="시설명")
    address: str = Field("", description="도로명 주소")
    category: str = Field("", description="대분류 (한국관광공사 코드 매핑)")
    sub_category: str = Field("", description="세부 분류 (카페/공원/숙박 등)")
    content_id: str = Field("", description="한국관광공사 콘텐츠 ID")
    lat: float = Field(0.0, description="위도 (WGS84)")
    lng: float = Field(0.0, description="경도 (WGS84)")
    tel: str = Field("", description="대표 전화")
    operation: str = Field("", description="운영시간/휴무일 정보")
    has_parking: str = Field("", description="주차 가능 여부 (Y/N/'')")
    indoor: str = Field("", description="실내 가능 (Y/N)")
    outdoor: str = Field("", description="실외 가능 (Y/N)")
    conditions: str = Field("", description="반려견 동반 시 제한사항 원문")
    description: str = Field("", description="장소 설명 텍스트")
    entrance_fee_amount: int | None = Field(None, description="입장료 (원). 미상이면 null")
    entrance_fee_type: str = Field("unknown", description="free/fixed/variable/conditional/unknown")
    extra_fee_amount: int | None = Field(None, description="강아지 추가요금 (원). 미상이면 null")
    extra_fee_type: str = Field("unknown", description="free/fixed/variable/conditional/unknown")
    match_source: str = Field("vector", description="매칭 경로 (name_exact | vector)")
    match_confidence: float = Field(0.0, description="매칭 신뢰도 (0.0~1.0)")


class MessageUpdate(BaseModel):
    """채팅 메시지 내용 수정 요청."""
    content: str = Field(..., min_length=1, description="수정할 메시지 본문")


class ChatTurnResponse(BaseModel):
    """
        user 메시지 저장 → 의도 분류 → 각 서비스 응답 생성 → assistant 메시지 저장까지 완료된 한 턴.

        POST /chat-rooms/{room_id}/messages 의 응답 스키마입니다.
    """

    user_message: MessageResponse = Field(..., description="저장된 사용자 메시지")
    assistant_message: MessageResponse = Field(..., description="저장된 assistant 응답 메시지")
    intent: IntentInfo = Field(..., description="의도 분류 결과")
    facility: FacilityCard | None = Field(
        None,
        description="시설정보 의도일 때만 채워지는 단일 시설 카드 페이로드 (그 외 null)",
    )
