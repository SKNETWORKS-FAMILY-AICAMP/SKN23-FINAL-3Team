# -*- coding: utf-8 -*-
"""
routers/chat_rooms.py
---------------------
채팅방 도메인 HTTP 엔드포인트.

엔드포인트:
    POST   /chat-rooms                    채팅방 생성 (title 미입력 시 자동 생성 예약)
    GET    /chat-rooms?user_id={id}       목록 (updated_at DESC)
    GET    /chat-rooms/{room_id}          단건 조회
    PATCH  /chat-rooms/{room_id}/title    제목 수정 (본인만)
    DELETE /chat-rooms/{room_id}          Soft Delete - 메시지는 보존 (본인만)
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from models.user import User
from schemas.chat_room import ChatRoomCreate, ChatRoomResponse, ChatRoomUpdateTitle
from services import chat_room_service as room_svc

router = APIRouter(tags=["ChatRooms"])


@router.post(
    "",
    response_model=ChatRoomResponse,
    status_code=status.HTTP_201_CREATED,
    summary="채팅방 생성",
    description=(
        "채팅방을 생성합니다.\n\n"
        "- `title` 미입력 시 `null`로 생성되며, "
        "첫 번째 메시지 발송 시 자동으로 제목이 설정됩니다."
    ),
)
async def create_room(
    data: ChatRoomCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatRoomResponse:
    room = await room_svc.create_room(data, db, current_user.id)
    return ChatRoomResponse.model_validate(room)


@router.get(
    "",
    response_model=list[ChatRoomResponse],
    summary="사용자별 채팅방 목록 조회",
    description="최근 메시지 발송 순(updated_at DESC)으로 정렬하여 반환합니다.",
)
async def list_rooms(
    user_id: Annotated[int, Query(description="조회할 사용자 ID")],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ChatRoomResponse]:
    rooms = await room_svc.list_rooms(user_id, db)
    return [ChatRoomResponse.model_validate(r) for r in rooms]


@router.get(
    "/{room_id}",
    response_model=ChatRoomResponse,
    summary="채팅방 단건 조회",
)
async def get_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ChatRoomResponse:
    room = await room_svc.get_room(room_id, db)
    return ChatRoomResponse.model_validate(room)


@router.patch(
    "/{room_id}/title",
    response_model=ChatRoomResponse,
    summary="채팅방 제목 수정",
    description="**본인 채팅방만 수정 가능** (다른 소유자 접근 시 403)",
)
async def update_room_title(
    room_id: int,
    data: ChatRoomUpdateTitle,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatRoomResponse:
    room = await room_svc.update_room_title(room_id, data, db, current_user.id)
    return ChatRoomResponse.model_validate(room)


@router.delete(
    "/{room_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="채팅방 삭제 (Soft Delete)",
    description=(
        "채팅방만 Soft Delete합니다. **하위 메시지는 삭제되지 않고 보존**됩니다.\n\n"
        "**본인 채팅방만 삭제 가능** (다른 소유자 접근 시 403)"
    ),
)
async def delete_room(
    room_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await room_svc.delete_room(room_id, db, current_user.id)
