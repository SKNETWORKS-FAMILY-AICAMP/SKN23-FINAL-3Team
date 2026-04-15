# -*- coding: utf-8 -*-
"""
services/chat_message.py
------------------------
채팅 메시지 도메인 서비스 레이어 (DB 쿼리 + 비즈니스 로직 통합).

주요 함수:
    - create_message() : 메시지 저장 + chat_rooms.updated_at 갱신
                       첫 메시지 발송 시 채팅방 제목 자동 생성
    - list_messages()  : 채팅방 전체 메시지 조회 (created_at ASC)
                       last_n 파라미터로 최근 N개만 조회 가능 (LLM 토큰 제한 대응)

[삭제 정책]
채팅 메시지는 삭제 없이 영구 보존합니다.

[제목 자동 생성]
채팅방 title이 None인 상태에서 첫 메시지가 발송되면,
메시지 content의 앞 100자를 채팅방 제목으로 자동 설정합니다.
"""

from __future__ import annotations

from datetime import datetime
from core.utils import kst_now
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.chat_message import ChatMessage
from schemas.chat_message import MessageCreate


async def create_message(
    room_id: int,
    data: MessageCreate,
    db: AsyncSession,
    current_user_id: int,
) -> ChatMessage:
    """
        채팅 메시지를 저장하고 채팅방의 updated_at을 현재 시각으로 갱신합니다.

        [자동 제목 생성]
        채팅방 title이 None인 경우, 첫 메시지 content의 앞 100자를 제목으로 설정합니다.

        [소유권 확인]
        채팅방의 소유자(room.user_id == current_user_id)만 메시지를 저장할 수 있습니다.

        Args:
                room_id        : 메시지를 저장할 채팅방 ID
                data           : MessageCreate 요청 데이터
                db             : AsyncSession
                current_user_id: 현재 로그인 사용자 ID

        Returns:
                저장된 ChatMessage ORM 객체

        Raises:
                HTTPException 403: 본인 채팅방 아님
                HTTPException 404: 채팅방 없음
    """
    # 순환 import 방지
    from services.chat_room_service import _assert_owner, get_room

    room = await get_room(room_id, db)
    _assert_owner(room, current_user_id)

    # 채팅방 제목 자동 생성 (첫 메시지 발송 시)
    if room.title is None:
        auto_title = data.content.strip()[:100]
        room.title = auto_title or "새 대화"

    # 메시지 저장
    message = ChatMessage(
        room_id=room_id,
        role=data.role,
        content=data.content,
    )
    db.add(message)

    # 채팅방 updated_at 갱신 (최근 메시지 순 정렬 기준)
    room.updated_at = kst_now()

    await db.flush()
    await db.refresh(message)

    return message


async def list_messages(
    room_id: int,
    db: AsyncSession,
    last_n: int | None = None,
) -> Sequence[ChatMessage]:
    """
        채팅방의 메시지 목록을 조회합니다.

        [정렬]
        모든 반환은 created_at ASC (시간순) 정렬입니다.
        LLM 컨텍스트로 사용할 때 이 순서 그대로 전달하면 됩니다.

        [last_n 파라미터]
        LLM 토큰 제한 대응용으로, 최근 N개만 조회할 수 있습니다.
        - last_n=10: 가장 최근 메시지 10개를 created_at ASC로 반환
        - last_n=None: 전체 메시지 반환

        Args:
                room_id: 채팅방 ID
                db     : AsyncSession
                last_n : 최근 N개 조회 (None이면 전체)

        Returns:
                ChatMessage ORM 객체 목록 (created_at ASC)

        Raises:
                HTTPException 404: 채팅방 없음
    """
    from services.chat_room_service import get_room

    # 채팅방 존재 확인
    await get_room(room_id, db)

    if last_n is not None and last_n > 0:
        # 최근 N개: DESC로 조회 후 Python에서 ASC 재정렬
        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.room_id == room_id)
            .order_by(ChatMessage.created_at.desc())
            .limit(last_n)
        )
        messages = list(result.scalars().all())
        return sorted(messages, key=lambda m: m.created_at)

    # 전체: ASC 정렬
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.room_id == room_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return result.scalars().all()
