# -*- coding: utf-8 -*-
"""
services/chat_room.py
---------------------
채팅방 도메인 서비스 레이어 (DB 쿼리 + 비즈니스 로직 통합).

주요 함수:
    - create_room()       : 채팅방 생성
    - list_rooms()        : 사용자별 목록 (updated_at DESC)
    - get_room()          : 단건 조회
    - update_room_title() : 제목 수정
    - delete_room()       : Soft Delete (하위 메시지는 물리 보존)

[소유권 정책]
채팅방의 수정 · 삭제는 생성한 사용자(room.user_id == current_user_id) 본인만 가능합니다.

[삭제 정책]
채팅방 Soft Delete 시 하위 chat_messages는 삭제되지 않고 물리적으로 보존됩니다.
(모델에서 cascade를 "save-update, merge"로 설정하여 delete 전파를 차단)
"""

from __future__ import annotations

from datetime import datetime
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat_room import ChatRoom
from schemas.chat_room import ChatRoomCreate, ChatRoomUpdateTitle


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────

def _assert_owner(room: ChatRoom, current_user_id: int) -> None:
    """요청자가 해당 채팅방의 소유자인지 검증합니다."""
    if room.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 채팅방만 수정/삭제할 수 있습니다.",
        )


# ── 공개 서비스 함수 ─────────────────────────────────────────────────────────

async def create_room(
    data: ChatRoomCreate,
    db: AsyncSession,
    current_user_id: int,
) -> ChatRoom:
    """
        채팅방을 생성합니다.

        title이 None이면 첫 번째 메시지 발송 시 자동으로 설정됩니다
        (services/chat_message.py 참조).

        Args:
                data           : ChatRoomCreate 요청 데이터
                db             : AsyncSession
                current_user_id: 현재 로그인 사용자 ID

        Returns:
                생성된 ChatRoom ORM 객체
    """
    room = ChatRoom(user_id=current_user_id, title=data.title)
    db.add(room)
    await db.flush()
    await db.refresh(room)

    return room


async def list_rooms(user_id: int, db: AsyncSession) -> Sequence[ChatRoom]:
    """
        사용자별 채팅방 목록 조회.

        - deleted_at IS NULL (삭제되지 않은 채팅방만)
        - updated_at 내림차순 (최근 메시지 순)

        Args:
                user_id: 조회할 사용자 ID
                db     : AsyncSession

        Returns:
                ChatRoom ORM 객체 목록
    """
    result = await db.execute(
        select(ChatRoom)
        .where(
            ChatRoom.user_id == user_id,
            ChatRoom.deleted_at.is_(None),
        )
        .order_by(ChatRoom.updated_at.desc())
    )
    return result.scalars().all()


async def get_room(room_id: int, db: AsyncSession) -> ChatRoom:
    """
        채팅방 단건 조회.

        Raises:
                HTTPException 404: 존재하지 않거나 삭제된 채팅방
    """
    result = await db.execute(
        select(ChatRoom).where(
            ChatRoom.id == room_id,
            ChatRoom.deleted_at.is_(None),
        )
    )
    room = result.scalar_one_or_none()

    if room is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"채팅방(id={room_id})을 찾을 수 없습니다.",
        )

    return room


async def update_room_title(
    room_id: int,
    data: ChatRoomUpdateTitle,
    db: AsyncSession,
    current_user_id: int,
) -> ChatRoom:
    """
        채팅방 제목을 수정합니다.

        Raises:
                HTTPException 403: 본인 채팅방 아님
                HTTPException 404: 채팅방 없음
    """
    room = await get_room(room_id, db)
    _assert_owner(room, current_user_id)

    room.title = data.title
    await db.flush()
    await db.refresh(room)

    return room


async def delete_room(
    room_id: int,
    db: AsyncSession,
    current_user_id: int,
) -> None:
    """
        채팅방 Soft Delete.

        하위 chat_messages는 삭제되지 않고 물리적으로 보존됩니다.

        Raises:
                HTTPException 403: 본인 채팅방 아님
                HTTPException 404: 채팅방 없음
    """
    room = await get_room(room_id, db)
    _assert_owner(room, current_user_id)

    room.deleted_at = datetime.utcnow()
    await db.flush()
