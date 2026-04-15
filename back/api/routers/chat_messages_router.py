# -*- coding: utf-8 -*-
"""
routers/chat_messages.py
------------------------
채팅 메시지 도메인 HTTP 엔드포인트.

이 라우터는 main.py에서 prefix="/chat-rooms" 로 등록됩니다.

엔드포인트:
    POST /chat-rooms/{room_id}/messages
            메시지 저장 (role: user | assistant | system)
            → 동시에 chat_rooms.updated_at 갱신
            → 채팅방 title이 None이면 첫 메시지로 자동 생성

    GET  /chat-rooms/{room_id}/messages
            전체 메시지 조회 (created_at ASC, LLM 컨텍스트용)

    GET  /chat-rooms/{room_id}/messages?last_n={N}
            최근 N개 메시지 조회 (created_at ASC, LLM 토큰 제한 대응)

[삭제 정책]
채팅 메시지는 삭제 엔드포인트를 제공하지 않습니다 (영구 보존).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from models.user import User
from schemas.chat_message import MessageCreate, MessageResponse
from services import chat_message_service as msg_svc

router = APIRouter(tags=["ChatMessages"])


@router.post(
    "/{room_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="채팅 메시지 저장",
    description=(
        "메시지를 저장하고 채팅방의 `updated_at`을 갱신합니다.\n\n"
        "- 채팅방 `title`이 `null`이면 첫 메시지 내용(앞 100자)으로 자동 설정됩니다.\n"
        "- `role`: `user` | `assistant` | `system`"
    ),
)
async def create_message(
    room_id: int,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    message = await msg_svc.create_message(room_id, data, db, current_user.id)
    return MessageResponse.model_validate(message)


@router.get(
    "/{room_id}/messages",
    response_model=list[MessageResponse],
    summary="채팅 메시지 목록 조회",
    description=(
        "채팅방의 메시지를 `created_at ASC`(시간순)으로 반환합니다.\n\n"
        "- `last_n` 미입력: 전체 메시지 반환\n"
        "- `last_n=N`: 가장 최근 N개만 반환 (LLM 토큰 제한 대응)\n"
        "  반환 순서는 항상 `created_at ASC`입니다."
    ),
)
async def list_messages(
    room_id: int,
    last_n: Annotated[
        int | None,
        Query(gt=0, description="최근 N개 조회 (미입력 시 전체 반환)"),
    ] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[MessageResponse]:
    messages = await msg_svc.list_messages(room_id, db, last_n=last_n)
    return [MessageResponse.model_validate(m) for m in messages]
