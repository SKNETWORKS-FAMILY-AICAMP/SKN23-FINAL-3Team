# -*- coding: utf-8 -*-
"""
services/chat_response_service.py
---------------------------------
의도 분류 결과에 따라 각 도메인 서비스로 요청을 라우팅하는 오케스트레이터.

분류 → 핸들러 매핑:
    - "다이어리 작성" → _handle_diary()  (다이어리 텍스트 + 이미지 생성 → S3 업로드 → URL 반환)
    - "장소추천"      → _handle_places(top_k=5)
    - "시설정보"      → _handle_facility(top_k=1)
    - "기타"          → _handle_fallback()  (인사, 케어 상담, 잡담 등 RAG 없이 GPT 직답)
    - (unknown)       → _handle_fallback()

dispatch() 는 DispatchContext(user_id, db) 를 선택 인자로 받아
다이어리 핸들러에서 사용자 반려견/이미지 DB 에 접근할 수 있도록 합니다.

장시간 블로킹 호출(RAG, GPT)은 asyncio.to_thread 로 스레드 풀에서 실행됩니다.
"""

from __future__ import annotations

import json
import base64
import logging
import asyncio

from datetime import date
from models.pet import Pet
from typing import Sequence
from sqlalchemy import select
from openai import AsyncOpenAI
from models.image import Image
from core.config import settings
from dataclasses import dataclass
from core.location.place import Place
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from services.image_service import _upload_to_s3
from services.intent_service import IntentResult, RAG_STRATEGY_MAP
from services.place_service import search_places_from_db
from fastapi import Request

# from ai.llm.prompts.diary_prompt import build_diary_prompt, build_final_image_prompt

from ai.prompts.diary_prompt_builder import DiaryPromptBuilder
_diary_prompt_builder = DiaryPromptBuilder()

logger = logging.getLogger(__name__)


# ── OpenAI 클라이언트 (lazy singleton) ───────────────────────────────────────
_openai_client: AsyncOpenAI | None = None
_GPT_MODEL = settings.GPT_MODEL
_IMAGE_MODEL = settings.DIARY_IMAGE_MODEL


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# ── 디스패치 컨텍스트 ────────────────────────────────────────────────────────
@dataclass
class DispatchContext:
    """
        핸들러에 사용자/DB 컨텍스트를 전달하는 컨테이너.
        장소/시설 핸들러는 무시하지만, 다이어리 핸들러는 user_id 로 반려견을 조회합니다.
    """
    user_id: int | None = None
    db: AsyncSession | None = None
    room_id: int | None = None  # 이전 대화 맥락 조회용


# ── 다이어리 의도 세부 키워드 분류 ──────────────────────────────────────────
_GUIDE_WRITE_KEYWORDS = [
    "어떻게", "방법", "어떡해", "알려줘", "알려주세요", "사용법", "처음",
    "어떻게 써", "어떻게 쓰", "어떻게 만들", "가이드", "도움말", "how",
    "모르겠", "모르겠어", "모르는데", "어떡해야", "어떻게 해야",
]
_GUIDE_ALBUM_KEYWORDS = [
    "앨범", "모아보기", "저장된", "쓴 일기", "다 쓴", "완성된", "기록",
    "어디서 봐", "어디에서 봐", "어디서 볼", "볼 수 있", "어디 있",
    "어디서 확인", "어디에서 확인", "찾을 수", "보관",
]
_GUIDE_CALENDAR_KEYWORDS = [
    "캘린더", "달력", "날짜별", "월별", "날짜로",
]

# 이전 봇 메시지에서 추가질문 요청 여부 감지
_FOLLOW_UP_MARKERS = [
    "더 이야기해주시면", "어디에 갔나요", "조금 더 알려주시면",
    "무슨 일이 있었나요", "특별히 기억에 남는",
]


def _detect_diary_sub_intent(query: str) -> str:
    """
    '다이어리 작성' 의도의 세부 분류.
    Returns: 'guide_write' | 'guide_album' | 'guide_calendar' | 'write'
    """
    q = query
    if any(kw in q for kw in _GUIDE_CALENDAR_KEYWORDS):
        return "guide_calendar"
    if any(kw in q for kw in _GUIDE_ALBUM_KEYWORDS):
        return "guide_album"
    if any(kw in q for kw in _GUIDE_WRITE_KEYWORDS):
        return "guide_write"
    return "write"


# ── 안내 응답 (정적, GPT 호출 없음) ─────────────────────────────────────────
_RESPONSE_GUIDE_WRITE = """\
그림일기는 두 가지 방법으로 쓸 수 있어요! ✍️

**방법 1 · 대화로 바로 쓰기**
여기 채팅창에 오늘 있었던 일을 말씀해주세요.
예) "오늘 강아지랑 한강 공원 산책했어요"
→ 제가 바로 그림일기를 만들어드려요!

**방법 2 · 단계별로 쓰기**
왼쪽 [강아지 일기장] 메뉴 → [새 그림일기 쓰기]를 누르면
일기 유형 선택 → 질문 답변 → 감정 선택 순서로
조금 더 자세하고 예쁜 일기를 만들 수 있어요 🐾

오늘 어떤 하루를 보내셨나요?"""

_RESPONSE_GUIDE_ALBUM = """\
다 쓴 일기는 두 곳에서 확인할 수 있어요! 📂

**📸 앨범** — [강아지 일기장] → [일기 모아보기]
날짜별로 그림일기를 모아서 볼 수 있어요.
일기를 누르면 그림과 내용을 크게 볼 수 있고, 수정도 가능해요.

**📅 캘린더** — 상단 메뉴 [캘린더]
캘린더 형식으로 날짜마다 기록을 확인할 수 있어요.

오늘 새 일기를 써드릴까요? 😊"""

_RESPONSE_GUIDE_CALENDAR = """\
📅 **캘린더**는 상단 메뉴의 [캘린더]에서 볼 수 있어요!

한 달치 기록을 달력 형식으로 한눈에 볼 수 있고,
날짜를 누르면 그날 쓴 그림일기를 바로 확인할 수 있어요 🐾

오늘 일기도 써드릴까요?"""


# ── 시스템 프롬프트 ──────────────────────────────────────────────────────────
_PLACES_SYSTEM_PROMPT = (
    "너는 반려견 동반 가능 장소를 추천하는 큐레이터야. "
    "검색된 장소 목록을 참고해 사용자에게 자연스러운 한국어로 2~3곳을 추천하되 "
    "각 장소의 특징(카테고리/위치/실내외 여부 등)을 간결하게 곁들여줘."
)

_FACILITY_SYSTEM_PROMPT = (
    "너는 반려견 동반 가능 시설의 상세 정보를 안내하는 챗봇이야. "
    "검색된 시설 한 곳의 정보를 바탕으로 운영시간·주소·주차·이용조건을 사용자가 이해하기 쉽게 설명해."
)

_FALLBACK_SYSTEM_PROMPT = (
    "너는 반려견 보호자를 돕는 친절한 한국어 챗봇 'withDOG' 이야. "
    "사용자의 질문에 간결하고 따뜻하게 답변해."
)



def _format_places_brief(places: Sequence[dict]) -> str:
    """검색된 장소를 프롬프트에 넣을 간단한 텍스트로 포맷."""
    if not places:
        return "(검색 결과 없음)"
    lines = []
    for p in places:
        parts = [
            f"- {p.get('name', '이름미상')}",
            f"({p.get('category', '')}, {p.get('city', '')})",
        ]
        if p.get("address"):
            parts.append(f"주소: {p['address']}")
        if p.get("open_hours"):
            parts.append(f"운영: {p['open_hours']}")
        if p.get("parking"):
            parts.append(f"주차: {p['parking']}")
        lines.append(" · ".join(parts))
    return "\n".join(lines)


async def _chat_completion(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 600,
) -> str:
    """OpenAI chat.completions 호출 래퍼 (예외 시 사용자 친화 메시지 반환)."""
    try:
        client = _get_openai_client()
        resp = await client.chat.completions.create(
            model=model or _GPT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.7,
            max_tokens=max_tokens,
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.error(f"[ChatResponse] LLM 호출 실패: {e}")
        return "죄송해요, 지금은 응답을 만들지 못했어요. 잠시 후 다시 시도해주세요."


# ── 다이어리 헬퍼 ────────────────────────────────────────────────────────────
_DEFAULT_DIARY_PET = {
    "pet_name": "우리 아이",
    "breed": "강아지",
    "breed_en": None,
    "birth_date": None,
    "personalities": [],
    "owner_name": "",
}
_DEFAULT_DIARY_TYPE = "daily"
_DEFAULT_DIARY_EMOTION = "😊"

# 한글 이모티콘 후보 — 메시지에서 감정 이모지를 가볍게 감지
_EMOTION_CANDIDATES = ["😊", "😌", "🥹", "😴", "😟", "🤍"]
# diary_type 키워드 힌트
_DIARY_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "memory": ("여행", "처음", "추억", "기념", "특별"),
    "owner":  ("나랑", "함께", "같이", "우리", "교감", "포근"),
    "dog":    ("간식", "산책", "공놀이", "뛰어", "짖"),
    "daily":  ("평범", "일상", "하루", "루틴"),
}


def _infer_emotion(text: str) -> str:
    for emoji in _EMOTION_CANDIDATES:
        if emoji in text:
            return emoji
    return _DEFAULT_DIARY_EMOTION


def _infer_diary_type(text: str) -> str:
    for dtype, keywords in _DIARY_TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return dtype
    return _DEFAULT_DIARY_TYPE


async def _load_pet_context(ctx: DispatchContext) -> dict:
    """
        ctx.user_id 로 사용자의 첫 번째 반려견을 조회하여
        diary_prompt 입력에 필요한 필드 딕셔너리로 변환합니다.
        조회 실패 시 기본값을 반환합니다.
    """
    if ctx.user_id is None or ctx.db is None:
        return dict(_DEFAULT_DIARY_PET)

    try:
        result = await ctx.db.execute(
            select(Pet)
            .where(Pet.user_id == ctx.user_id)
            .options(selectinload(Pet.breed))
            .order_by(Pet.id.asc())
            .limit(1)
        )
        pet = result.scalar_one_or_none()
    except Exception as e:
        logger.warning(f"[Diary] 반려견 조회 실패: {e}")
        return dict(_DEFAULT_DIARY_PET)

    if pet is None:
        return dict(_DEFAULT_DIARY_PET)

    breed_ko = getattr(pet.breed, "name_ko", None) if pet.breed else None
    breed_en = getattr(pet.breed, "name_en", None) if pet.breed else None
    birth_str: str | None = None
    if isinstance(pet.birth_date, date):
        birth_str = pet.birth_date.strftime("%Y-%m-%d")

    return {
        "pet_name": pet.name or _DEFAULT_DIARY_PET["pet_name"],
        "breed": breed_ko or _DEFAULT_DIARY_PET["breed"],
        "breed_en": breed_en,
        "birth_date": birth_str,
        "personalities": list(pet.selected_tags or []),
        "owner_name": "",
    }


async def _generate_diary_json(pet_ctx: dict, query: str) -> dict | None:
    """build_diary_prompt → GPT 호출 → JSON 파싱."""

    emotion = _infer_emotion(query)
    diary_type = _infer_diary_type(query)
    conversation_summary = f"보호자: {query.strip()}"
    prompt = _diary_prompt_builder.build_diary_prompt(
    # prompt = build_diary_prompt(
        pet_name=pet_ctx["pet_name"],
        breed=pet_ctx["breed"],
        birth_date=pet_ctx["birth_date"],
        personalities=pet_ctx["personalities"],
        owner_name=pet_ctx["owner_name"],
        diary_type=diary_type,
        emotion=emotion,
        conversation_summary=conversation_summary,
    )

    try:
        client = _get_openai_client()
        resp = await client.chat.completions.create(
            model=_GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        raw = (resp.choices[0].message.content or "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
    except Exception as e:
        logger.error(f"[Diary] 일기 생성/파싱 실패: {e}")
        return None

    data["_emotion"] = emotion
    data["_diary_type"] = diary_type
    data["_conversation"] = conversation_summary
    return data


async def _generate_and_store_image(
    pet_ctx: dict,
    diary_data: dict,
    ctx: DispatchContext,
) -> str | None:
    """
        build_final_image_prompt → OpenAI 이미지 생성 → S3 업로드 → images 테이블 저장.
        실패 시 None 을 반환하고 호출 측에서 이미지 없이 응답합니다.
    """
    image_prompt = _diary_prompt_builder.build_final_image_prompt(
    # image_prompt = build_final_image_prompt(
        image_prompt_base=diary_data.get("image_prompt_base", ""),
        breed=pet_ctx["breed"],
        breed_en=pet_ctx["breed_en"],
        birth_date=pet_ctx["birth_date"],
        personalities=pet_ctx["personalities"],
        all_answers=[diary_data.get("_conversation", "")],
        emotion=diary_data.get("_emotion", _DEFAULT_DIARY_EMOTION),
    )

    # 1) 이미지 생성 (base64)
    try:
        client = _get_openai_client()
        resp = await client.images.generate(
            model=_IMAGE_MODEL,
            prompt=image_prompt,
            size="1024x1024",
            quality="low",
            n=1,
        )
        b64 = resp.data[0].b64_json
        if not b64:
            logger.error("[Diary] 이미지 생성 실패: b64_json 누락")
            return None
    except Exception as e:
        logger.error(f"[Diary] 이미지 생성 호출 실패: {e}")
        return None

    # 2) S3 업로드 + DB 저장 (ctx.db 있을 때만)
    try:
        image_bytes = base64.b64decode(b64)
        file_url = await _upload_to_s3(image_bytes, "diary.png", "image/png")
    except Exception as e:
        logger.error(f"[Diary] S3 업로드 실패: {e}")
        return None

    if ctx.db is not None:
        try:
            image_row = Image(file_url=file_url, file_name="diary.png")
            ctx.db.add(image_row)
            await ctx.db.flush()
        except Exception as e:
            logger.warning(f"[Diary] images 테이블 저장 실패 (URL 만 반환): {e}")

    return file_url


# ── 의도별 핸들러 ────────────────────────────────────────────────────────────
async def _handle_diary(query: str, ctx: DispatchContext) -> str:
    """
        사용자 메시지를 바탕으로 그림일기(텍스트 + 이미지)를 생성합니다.

        흐름:
            1. ctx.user_id 로 반려동물 컨텍스트 확보 (없으면 기본값)
            2. build_diary_prompt → GPT (_GPT_MODEL) → 일기 JSON
            3. build_final_image_prompt → OpenAI Images → base64
            4. base64 → S3 업로드 → images 테이블 저장
            5. 일기 텍스트 + 이미지 URL(마크다운)을 assistant 응답으로 반환

        어떤 단계든 실패하면 가능한 만큼만 반환합니다
        (텍스트 실패 → 안내 문구, 이미지 실패 → 텍스트만 반환).
    """
    pet_ctx = await _load_pet_context(ctx)
    diary_data = await _generate_diary_json(pet_ctx, query)

    if diary_data is None:
        return (
            "일기 생성에 실패했어요. 잠시 후 다시 시도하거나 "
            "/api/diary/generate 엔드포인트에서 직접 작성해주세요."
        )

    title = diary_data.get("title", "오늘의 일기")
    content = diary_data.get("content", "")
    summary = diary_data.get("summary", "")

    # 이미지 생성은 실패해도 텍스트 응답은 유지
    image_url = await _generate_and_store_image(pet_ctx, diary_data, ctx)

    lines = [f"📖 **{title}**", "", content]
    if summary:
        lines.extend(["", f"_요약_: {summary}"])
    if image_url:
        lines.extend(["", f"![{title}]({image_url})"])
    else:
        lines.extend(["", "(이미지 생성은 실패했어요. 나중에 다시 시도해주세요.)"])

    return "\n".join(lines)


async def _handle_places(query: str, ctx: DispatchContext, top_k: int = 5, request: Request = None) -> str:
    if settings.USE_DUMMY_PLACES:
        places = await Place().find_place(top_k=top_k)
    elif ctx.db is not None:
        places = await search_places_from_db(query, ctx.db, n_results=top_k, request=request)
    else:
        logger.warning("[ChatResponse] db 세션 없음 — 장소 검색 불가")
        places = []

    places_text = _format_places_brief(places)
    user_prompt = f"사용자 질문: {query}\n\n[검색된 장소]\n{places_text}"
    return await _chat_completion(_PLACES_SYSTEM_PROMPT, user_prompt)


async def _handle_facility(query: str, ctx: DispatchContext) -> str:
    if settings.USE_DUMMY_PLACES:
        places = await Place().find_place(top_k=1)
    elif ctx.db is not None:
        places = await search_places_from_db(query, ctx.db, n_results=1)
    else:
        logger.warning("[ChatResponse] db 세션 없음 — 시설 검색 불가")
        places = []

    places_text = _format_places_brief(places)
    user_prompt = f"사용자 질문: {query}\n\n[검색된 시설]\n{places_text}"
    return await _chat_completion(_FACILITY_SYSTEM_PROMPT, user_prompt)


async def _handle_fallback(query: str) -> str:
    return await _chat_completion(_FALLBACK_SYSTEM_PROMPT, query)


async def _handle_diary_mini_flow(query: str, ctx: DispatchContext) -> str:
    """
    실제 일기 작성 의도일 때:
    - 이전 봇 메시지가 추가 질문이었으면 → 그 답변으로 일기 생성
    - 입력이 충분히 길면 (20자 이상) → 바로 생성
    - 짧으면 → 추가 질문 1개로 컨텍스트 보강 요청
    """
    # 이전 봇 메시지가 추가질문 요청이었는지 확인 (채팅방 히스토리)
    if ctx.db is not None and ctx.room_id is not None:
        try:
            from services.chat_message_service import list_messages
            recent = await list_messages(ctx.room_id, ctx.db, last_n=4)
            bot_messages = [m for m in recent if m.role == "assistant"]
            if bot_messages:
                last_bot = bot_messages[-1].content
                if any(marker in last_bot for marker in _FOLLOW_UP_MARKERS):
                    logger.info("[DiaryMiniFlow] 이전 추가질문 → 현재 메시지로 일기 생성")
                    return await _handle_diary(query, ctx)
        except Exception as e:
            logger.warning(f"[DiaryMiniFlow] 히스토리 조회 실패: {e}")

    # 입력이 충분히 구체적이면 바로 생성
    if len(query.strip()) >= 20:
        return await _handle_diary(query, ctx)

    # 짧은 입력 → 추가 질문으로 컨텍스트 보강
    pet_ctx = await _load_pet_context(ctx)
    pet_name = pet_ctx.get("pet_name", "우리 아이")
    return (
        f"{pet_name}와 함께한 오늘 하루를 일기로 만들어드릴게요! ✍️\n\n"
        "조금 더 알려주시면 더 예쁜 일기를 쓸 수 있어요 😊\n\n"
        "어디에 갔나요? 무슨 일이 있었나요? 특별히 기억에 남는 순간이 있었나요?"
    )


# ── 공개 디스패처 ────────────────────────────────────────────────────────────
async def dispatch(
    intent_result: IntentResult,
    query: str,
    ctx: DispatchContext | None = None,
    request: Request = None,
) -> str:
    """
        의도 분류 결과에 따라 적절한 핸들러로 라우팅하고 assistant 응답 텍스트를 반환합니다.

        '다이어리 작성' 의도는 키워드 후처리로 세분화됩니다:
            - guide_write    → 일기 쓰는 방법 안내 (정적 응답)
            - guide_album    → 앨범/캘린더 위치 안내 (정적 응답)
            - guide_calendar → 캘린더 위치 안내 (정적 응답)
            - write          → 미니 플로우 (컨텍스트 부족 시 추가 질문 → 일기 생성)
    """
    if ctx is None:
        ctx = DispatchContext()

    intent = intent_result.intent
    logger.info(f"[ChatResponse] 의도: {intent}")
    top_k = int(intent_result.strategy.get("top_k", 5))

    if intent == "다이어리 작성":
        sub = _detect_diary_sub_intent(query)
        logger.info(f"[ChatResponse] 다이어리 세부 의도: {sub}")
        if sub == "guide_write":
            return _RESPONSE_GUIDE_WRITE
        if sub == "guide_album":
            return _RESPONSE_GUIDE_ALBUM
        if sub == "guide_calendar":
            return _RESPONSE_GUIDE_CALENDAR
        return await _handle_diary_mini_flow(query, ctx)

    if intent == "장소추천":
        return await _handle_places(query, ctx, top_k=top_k, request=request)
    if intent == "시설정보":
        return await _handle_facility(query, ctx)
    if intent == "기타" or intent not in RAG_STRATEGY_MAP:
        logger.info("[Dispatch] 기타 분기 처리")
        return await _handle_fallback(query)

    logger.warning(f"[ChatResponse] 알 수 없는 의도: {intent} → fallback 처리")
    return await _handle_fallback(query)
