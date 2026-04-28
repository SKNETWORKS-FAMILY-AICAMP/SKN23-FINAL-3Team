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
