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


class MessageResponse(BaseModel):
    """채팅 메시지 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="메시지 ID")
    room_id: int = Field(..., description="채팅방 ID")
    role: str = Field(..., description="발신자 구분 (user | assistant | system)")
    content: str = Field(..., description="메시지 본문")
    created_at: datetime = Field(..., description="발송 일시")
