# -*- coding: utf-8 -*-
"""
schemas/chat_room.py
--------------------
채팅방 도메인 Pydantic v2 스키마.

- ChatRoomCreate      : 채팅방 생성 요청
- ChatRoomUpdateTitle : 채팅방 제목 수정 요청
- ChatRoomResponse    : 응답 스키마
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatRoomCreate(BaseModel):
    """채팅방 생성 요청. 제목 미입력 시 첫 메시지 발송 후 자동 생성됩니다."""

    title: str | None = Field(
        None,
        max_length=200,
        description="채팅방 제목 (미입력 시 첫 메시지 내용으로 자동 설정)",
    )


class ChatRoomUpdateTitle(BaseModel):
    """채팅방 제목 수정 요청."""

    title: str = Field(..., min_length=1, max_length=200, description="새 채팅방 제목")


class ChatRoomResponse(BaseModel):
    """채팅방 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="채팅방 ID")
    user_id: int = Field(..., description="사용자 ID")
    title: str | None = Field(None, description="채팅방 제목")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="마지막 메시지 발송 일시")
