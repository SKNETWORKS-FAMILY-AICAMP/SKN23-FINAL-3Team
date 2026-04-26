# -*- coding: utf-8 -*-
"""
routers/chat_messages.py
------------------------
채팅 메시지 도메인 HTTP 엔드포인트.

이 라우터는 main.py에서 prefix="/chat-rooms" 로 등록됩니다.

엔드포인트:
    POST /chat-rooms/{room_id}/messages
            사용자 메시지 저장 → 의도 분류(KoELECTRA) → 각 서비스 디스패치
            → assistant 응답 메시지 저장까지 한 턴 처리
            → chat_rooms.updated_at 갱신 및 title 자동 생성
            → role 은 'user' 로 고정됨 (다른 role 은 400)

    GET  /chat-rooms/{room_id}/messages
            전체 메시지 조회 (created_at ASC, LLM 컨텍스트용)

    GET  /chat-rooms/{room_id}/messages?last_n={N}
            최근 N개 메시지 조회 (created_at ASC, LLM 토큰 제한 대응)

[삭제 정책]
채팅 메시지는 삭제 엔드포인트를 제공하지 않습니다 (영구 보존).
"""

from __future__ import annotations

from typing import Annotated
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession
from core.deps import get_current_user, get_db
from services import chat_message_service as msg_svc
from fastapi import APIRouter, Depends, Query, Request, status
from schemas.chat_message import (ChatTurnResponse, IntentInfo, MessageCreate, MessageResponse)

router = APIRouter(tags=["ChatMessages"])


@router.post(
    "/{room_id}/messages",
    response_model=ChatTurnResponse,
    status_code=status.HTTP_201_CREATED,
    summary="채팅 메시지 전송 (의도 분류 + 응답 생성)",
    description=(
        "사용자 메시지를 저장하고 한 턴을 완결합니다.\n\n"
        "1. role='user' 메시지 저장 (다른 role 은 400)\n"
        "2. KoELECTRA 의도 분류 (`다이어리 작성` / `장소추천` / `시설정보`)\n"
        "3. 의도에 맞는 도메인 서비스(placeRAG/LLM)로 라우팅하여 응답 생성\n"
        "4. role='assistant' 메시지 저장\n"
        "5. `chat_rooms.updated_at` 갱신, `title` 이 null 이면 첫 메시지로 자동 설정\n\n"
        "응답에는 저장된 user/assistant 메시지와 의도 분류 결과가 함께 포함됩니다."
    ),
)
async def create_message(
    room_id: int,
    data: MessageCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatTurnResponse:
    user_msg, assistant_msg, intent_result = await msg_svc.create_message_with_response(
        room_id, data, db, current_user.id, request=request
    )
    return ChatTurnResponse(
        user_message=MessageResponse.model_validate(user_msg),
        assistant_message=MessageResponse.model_validate(assistant_msg),
        intent=IntentInfo(
            intent=intent_result.intent,
            confidence=intent_result.confidence,
        ),
    )


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
