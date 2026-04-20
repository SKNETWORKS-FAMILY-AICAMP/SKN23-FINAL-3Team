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
    from ai.llm.prompts.diary_prompt import build_diary_prompt

    emotion = _infer_emotion(query)
    diary_type = _infer_diary_type(query)
    conversation_summary = f"보호자: {query.strip()}"

    prompt = build_diary_prompt(
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
    from ai.llm.prompts.diary_prompt import build_final_image_prompt

    image_prompt = build_final_image_prompt(
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


async def _handle_places(query: str, ctx: DispatchContext, top_k: int = 5) -> str:
    if settings.USE_DUMMY_PLACES:
        places = await Place().find_place(top_k=top_k)
    elif ctx.db is not None:
        places = await search_places_from_db(query, ctx.db, n_results=top_k)
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


# ── 공개 디스패처 ────────────────────────────────────────────────────────────
async def dispatch(
    intent_result: IntentResult,
    query: str,
    ctx: DispatchContext | None = None,
) -> str:
    """
        의도 분류 결과에 따라 적절한 핸들러로 라우팅하고 assistant 응답 텍스트를 반환합니다.

        Args:
                intent_result: intent_service.classify_intent_async() 결과
                query        : 사용자 입력 텍스트
                ctx          : DispatchContext(user_id, db) — 다이어리 핸들러에서 사용

        Returns:
                assistant 응답 문자열 (항상 비어있지 않음)
    """
    if ctx is None:
        ctx = DispatchContext()

    intent = intent_result.intent

    logger.info(f"[ChatResponse] 의도: {intent}")

    top_k = int(intent_result.strategy.get("top_k", 5))

    if intent == "다이어리 작성":
        return await _handle_diary(query, ctx)
    if intent == "장소추천":
        return await _handle_places(query, ctx, top_k=top_k)
    if intent == "시설정보":
        return await _handle_facility(query, ctx)
    if intent == "기타" or intent not in RAG_STRATEGY_MAP:
        logger.info("[Dispatch] 기타 분기 처리")
        return await _handle_fallback(query)

    logger.warning(f"[ChatResponse] 알 수 없는 의도: {intent} → fallback 처리")
    return await _handle_fallback(query)
