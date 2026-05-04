# -*- coding: utf-8 -*-
"""
services/chat_message.py
------------------------
채팅 메시지 도메인 서비스 레이어 (DB 쿼리 + 비즈니스 로직 통합).

주요 함수:
    - create_message()               : 메시지 단건 저장 + chat_rooms.updated_at 갱신
    - create_message_with_response() : user 메시지 저장 → 의도 분류 → 각 서비스 디스패치
                                       → assistant 메시지 저장까지 한 턴 처리
    - list_messages()                : 채팅방 전체 메시지 조회 (created_at ASC)
                                       last_n 파라미터로 최근 N개만 조회 가능 (LLM 토큰 제한 대응)

[삭제 정책]
채팅 메시지는 삭제 없이 영구 보존합니다.

[제목 자동 생성]
채팅방 title이 None인 상태에서 첫 메시지가 발송되면,
메시지 content의 앞 100자를 채팅방 제목으로 자동 설정합니다.
"""

from __future__ import annotations

import logging

from typing import Sequence
from fastapi import Request
from sqlalchemy import select
from core.utils import kst_now
from models.chat_message import ChatMessage
from schemas.chat_message import MessageCreate
from sqlalchemy.ext.asyncio import AsyncSession
from services.chat_room_service import get_room
from services.intent_service import IntentResult
from services import chat_response_service, intent_service
from services.diary_response_service import is_diary_button_action, is_diary_confirm_request, is_diary_start_flow_request

logger = logging.getLogger(__name__)

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


async def create_message_with_response(
    room_id: int,
    data: MessageCreate,
    db: AsyncSession,
    current_user_id: int,
    request: Request | None = None,
) -> tuple[ChatMessage, ChatMessage, IntentResult, dict | None, list[dict] | None]:
    """
        사용자 메시지를 저장하고, 의도분류 → 도메인 서비스 디스패치를 거쳐
        assistant 응답 메시지를 저장한 뒤 관련 카드 페이로드와 함께 반환합니다.

        [처리 흐름]
            1. 채팅방 소유권/존재 확인 + 제목 자동 생성
            2. user 메시지 저장
            3. intent_service.classify_intent_async() 로 의도 분류
            4. chat_response_service.dispatch() 로 각 의도별 핸들러 호출
            5. assistant 메시지 저장
            6. chat_rooms.updated_at 갱신

        [오류 처리]
        의도 분류 또는 응답 생성에 실패하면 사용자 친화적 문구로 대체된
        assistant 메시지를 저장하고 분류 결과는 fallback 의도로 기록합니다.
        (사용자 메시지는 이미 저장되어 있으므로 트랜잭션은 커밋되어야 합니다.)

        Args:
                room_id        : 채팅방 ID
                data           : user 메시지 내용 (role 은 항상 'user' 로 강제됨)
                db             : AsyncSession
                current_user_id: 현재 로그인 사용자 ID

        Returns:
                (user_message, assistant_message, intent_result, facility, places)

        Raises:
                HTTPException 403: 본인 채팅방 아님
                HTTPException 404: 채팅방 없음
                HTTPException 400: user 가 아닌 role 로 요청한 경우
    """
    from fastapi import HTTPException, status as http_status
    from services.chat_room_service import _assert_owner, get_room

    if data.role != "user":
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="이 엔드포인트는 role='user' 메시지만 허용합니다.",
        )

    room = await get_room(room_id, db)
    _assert_owner(room, current_user_id)

    # 채팅방 제목 자동 생성 (첫 메시지 발송 시)
    if room.title is None:
        auto_title = data.content.strip()[:100]
        room.title = auto_title or "새 대화"

    # 1) user 메시지 저장
    user_message = ChatMessage(
        room_id=room_id,
        role="user",
        content=data.content,
    )
    db.add(user_message)
    await db.flush()
    await db.refresh(user_message)

    # 2) 의도 분류 → 도메인 서비스 디스패치
    try:
        intent_result = await intent_service.classify_intent_async(data.content)
    except Exception as e:
        logger.error(f"[ChatMessage] 의도 분류 실패: {e}")
        # fallback: 기본 의도(장소추천)로 처리 — dispatch 가 fallback 로직 내장
        intent_result = IntentResult(
            intent="unknown",
            confidence=0.0,
            strategy=intent_service.RAG_STRATEGY_MAP["장소추천"],
        )
        
    # diary 버튼 액션/확인/시작 요청은 dispatch 에서 바로 처리되므로
    # 클라이언트에 반환하는 intent 도 '다이어리 작성'으로 맞춰줌
    # (KoELECTRA 가 '장소추천' 등으로 잘못 분류해도 프론트가 searchPlaces 호출하지 않도록)
    if is_diary_button_action(data.content) or is_diary_confirm_request(data.content) or is_diary_start_flow_request(data.content):
        logger.info(f"[ChatMessage] diary 버튼/확인 액션 → intent 강제 재정의: {data.content!r}")
        intent_result = IntentResult(
            intent="다이어리 작성",
            confidence=1.0,
            strategy=intent_service.RAG_STRATEGY_MAP.get("다이어리 작성", {}),
        )

    ctx = chat_response_service.DispatchContext(
        user_id=current_user_id,
        db=db,
        room_id=room_id,
        pet_id=data.pet_id,
        user_lat=data.user_lat,
        user_lng=data.user_lng,
    )
    dispatch_result = await chat_response_service.dispatch(
        intent_result,
        data.content,
        ctx,
        request=request,
    )
    assistant_text = dispatch_result.text or "죄송해요, 응답을 만들지 못했어요. 잠시 후 다시 시도해주세요."
    facility = dispatch_result.facility
    places = dispatch_result.places

    # 3) assistant 메시지 저장
    assistant_message = ChatMessage(
        room_id=room_id,
        role="assistant",
        content=assistant_text,
    )
    db.add(assistant_message)

    # 채팅방 updated_at 갱신
    room.updated_at = kst_now()

    await db.flush()
    await db.refresh(assistant_message)

    return user_message, assistant_message, intent_result, facility, places


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


async def update_message_content(
    room_id: int,
    message_id: int,
    new_content: str,
    db: AsyncSession,
    current_user_id: int,
) -> ChatMessage:
    """assistant 메시지 내용을 수정합니다 (장소 추천 후 표시 내용 동기화용)."""
    from services.chat_room_service import _assert_owner, get_room

    room = await get_room(room_id, db)
    _assert_owner(room, current_user_id)

    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.id == message_id,
            ChatMessage.room_id == room_id,
        )
    )
    message = result.scalar_one_or_none()
    if message is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="메시지를 찾을 수 없습니다.")

    message.content = new_content
    await db.flush()
    await db.refresh(message)
    return message
