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

from pydantic import BaseModel, ConfigDict, Field, field_validator

from utils.validation import clean_text


class ChatRoomCreate(BaseModel):
    """채팅방 생성 요청. 제목 미입력 시 첫 메시지 발송 후 자동 생성됩니다."""

    title: str | None = Field(
        None,
        description="채팅방 제목 (0~50자, 미입력 시 자동. 욕설 검사는 service 단)",
    )

    @field_validator("title", mode="before")
    @classmethod
    def _clean_title(cls, v: str | None) -> str | None:
        return clean_text(v, min_length=0, max_length=50, label="채팅방 제목", allow_blank=True)


class ChatRoomUpdateTitle(BaseModel):
    """채팅방 제목 수정 요청."""

    title: str = Field(..., description="새 채팅방 제목 (1~50자, 욕설 검사는 service 단)")

    @field_validator("title", mode="before")
    @classmethod
    def _clean_title(cls, v: str) -> str:
        cleaned = clean_text(v, min_length=1, max_length=50, label="채팅방 제목")
        # required 필드 — clean_text 가 None 반환할 일은 없음 (str 만 들어옴)
        assert cleaned is not None
        return cleaned


class ChatRoomResponse(BaseModel):
    """채팅방 응답 스키마."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="채팅방 ID")
    user_id: int = Field(..., description="사용자 ID")
    title: str | None = Field(None, description="채팅방 제목")
    created_at: datetime = Field(..., description="생성 일시")
    updated_at: datetime = Field(..., description="마지막 메시지 발송 일시")
