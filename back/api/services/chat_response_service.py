# -*- coding: utf-8 -*-
"""
services/chat_response_service.py
---------------------------------
의도 분류 결과에 따라 각 도메인 서비스로 요청을 라우팅하는 오케스트레이터.

분류 → 핸들러 매핑:
    - "다이어리 작성" → diary_response_service 로 위임
    - "장소추천"      → _handle_places(top_k=5)
    - "시설정보"      → _handle_facility(top_k=1)
    - "기타"          → _handle_fallback()
    - (unknown)       → _handle_fallback()
"""

from __future__ import annotations

import logging

from dataclasses import dataclass
from typing import Sequence

from fastapi import Request
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.location.place import Place
from services.intent_service import IntentResult, RAG_STRATEGY_MAP
from services.place_service import SEOUL, _parse_query_with_llm, search_places_from_db
from fastapi import Request

# from ai.llm.prompts.diary_prompt import build_diary_prompt, build_final_image_prompt

from ai.prompts.diary_prompt_builder import DiaryPromptBuilder
_diary_prompt_builder = DiaryPromptBuilder()
from services.place_service import search_places_from_db
from services.diary_response_service import (
    detect_diary_sub_intent,
    get_diary_guide_response,
    handle_diary_response,
    is_diary_button_action,
    is_diary_confirm_request,
)

logger = logging.getLogger(__name__)

_openai_client: AsyncOpenAI | None = None
_GPT_MODEL = settings.GPT_MODEL
_IMAGE_MODEL = settings.DIARY_IMAGE_MODEL
_OUT_OF_SERVICE_AREA_MESSAGE = "현재 서비스는 서울 지역만 지원하고 있습니다."


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


@dataclass
class DispatchContext:
    """
    핸들러에 사용자/DB 컨텍스트를 전달하는 컨테이너.
    diary_response_service 는 duck typing 으로 이 값을 사용합니다.
    """
    user_id: int | None = None
    db: AsyncSession | None = None
    room_id: int | None = None


_PLACES_SYSTEM_PROMPT = (
    "너는 반려견 동반 가능 장소를 추천하는 큐레이터야. "
    "검색된 장소 목록을 참고해 사용자에게 자연스러운 한국어로 2~3곳을 추천하되 "
    "각 장소의 특징(카테고리/위치/실내외 여부 등)을 간결하게 곁들여줘. "
    "만약 '[검색 결과 없음]'이 표시되면, 조건에 맞는 장소를 찾지 못했다고 안내하고 "
    "현재 서비스는 서울 지역만 지원하므로 다른 지역 요청인 경우 그 점을 친절하게 알려줘."
)

_FACILITY_SYSTEM_PROMPT = (
    "너는 반려견 동반 가능 시설의 상세 정보를 안내하는 챗봇이야. "
    "검색된 시설 한 곳의 정보를 바탕으로 운영시간·주소·주차·이용조건을 사용자가 이해하기 쉽게 설명해."
)

_FALLBACK_SYSTEM_PROMPT = (
    "너는 반려견 보호자를 돕는 친절한 한국어 챗봇 'withDOG' 이야. "
    "사용자의 질문에 간결하고 따뜻하게 답변해."
)



_PLACE_REASON_SYSTEM_PROMPT = (
    "당신은 반려견 동반 장소를 추천하는 도우미입니다. "
    "사용자 질문과 후보 장소 정보를 보고 각 장소마다 질문 맥락에 맞는 추천 이유를 1문장으로 작성하세요. "
    "운영시간, 실내/실외 여부, 주차, 카테고리, 설명 중 실제로 주어진 정보만 활용하고 추측은 하지 마세요. "
    "비용, 입장료, 추가요금 관련 질문일 때는 entrance_fee와 extra_fee 필드가 실제로 있을 때만 그 정보를 근거로 설명하세요. "
    "주차 가능 여부만으로 비용이 없다고 말하거나, 비용 정보를 추측해서 말하지 마세요. "
    "모든 장소의 reason은 서로 다르게 쓰고, 질문에 나온 조건이 반영되도록 자연스럽게 설명하세요. "
    '반드시 JSON만 반환하세요. 형식은 {"places":[{"name":"장소명","reason":"추천 이유"}]} 입니다.'
)


def _format_places_brief(places: Sequence[dict]) -> str:
    if not places:
        return "(검색 결과 없음)"
    lines = []
    for p in places:
        parts = [
            f"- {p.get('name', '이름미상')}",
            f"({p.get('category', '')}, {p.get('sub_category', '')})",
        ]
        if p.get("address"):
            parts.append(f"주소: {p['address']}")
        if p.get("operation"):
            parts.append(f"운영: {p['operation']}")
        if p.get("has_parking"):
            parts.append(f"주차: {p['has_parking']}")
        if p.get("conditions"):
            parts.append(f"이용조건: {p['conditions']}")
        lines.append(" · ".join(parts))
    return "\n".join(lines)


def _format_place_list_response(places: Sequence[dict]) -> str:
    """Render a stable place response without a second LLM pass."""
    if not places:
        return (
            "조건에 맞는 장소를 찾지 못했어요. "
            "원하시는 지역이나 조건을 조금 바꿔서 다시 말씀해 주세요."
        )

    lines = ["반려견과 함께 가보기 좋은 장소를 정리했어요.", ""]
    for idx, place in enumerate(places, start=1):
        name = place.get("name", "이름 미상")
        address = place.get("address", "")
        reason = (place.get("reason") or "").strip()

        lines.append(f"{idx}. {name}")
        lines.append("")
        if address:
            lines.append(f"- 주소: {address}")
            lines.append("")
        if reason:
            lines.append(f"- 추천 이유: {reason}")
            lines.append("")

    lines.append("세부 정보는 아래 지도와 장소 카드에서 함께 확인해보세요.")
    return "\n".join(lines)


async def _chat_completion(
    system_prompt: str,
    user_prompt: str,
    *,
    model: str | None = None,
    max_tokens: int = 600,
) -> str:
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
def _format_places_for_reasoning(places: Sequence[dict]) -> str:
    if not places:
        return "[]"

    lines: list[str] = []
    for place in places:
        attrs = [
            f"name={place.get('name', '')}",
            f"category={place.get('category', '')}",
            f"sub_category={place.get('sub_category', '')}",
            f"address={place.get('address', '')}",
            f"operation={place.get('operation', '')}",
            f"indoor={place.get('indoor', '')}",
            f"outdoor={place.get('outdoor', '')}",
            f"has_parking={place.get('has_parking', '')}",
            f"conditions={place.get('conditions', '')}",
            f"restriction_tags={','.join(place.get('restriction_tags', []))}",
            f"entrance_fee={place.get('entrance_fee', '')}",
            f"extra_fee={place.get('extra_fee', '')}",
            f"description={place.get('description', '')}",
        ]
        lines.append(" | ".join(attrs))
    return "\n".join(lines)


async def generate_place_reasons(query: str, places: Sequence[dict]) -> dict[str, str]:
    """질문 맥락을 반영한 장소별 추천 이유를 LLM으로 생성한다."""
    if not places:
        return {}

    user_prompt = (
        f"사용자 질문:\n{query}\n\n"
        f"[후보 장소]\n{_format_places_for_reasoning(places)}\n\n"
        "모든 후보 장소에 대해 reason을 작성해 주세요."
    )

    user_prompt += (
        "\n\n[reason rules]\n"
        "- Use only details that directly match the user's request.\n"
        "- If the question is not about fees or cost, do not use entrance_fee or extra_fee in the reason.\n"
        "- If the question mentions waste bags, poop bags, or supplies, prioritize conditions/restrictions details over fee details.\n"
        "- If the question mentions leash, waste bags, supplies, or other restrictions, use conditions or restriction_tags as the main evidence.\n"
        "- Do not infer that a place is restriction-free just because conditions are empty.\n"
        "- Do not say a place allows off-leash or no-supplies-needed unless conditions or restriction_tags support that claim.\n"
        "- Do not explain why a place does not match. Explain only why the returned place matches.\n"
        "- Each place reason must be meaningfully different from the others.\n"
        "- Do not repeat the same sentence pattern for multiple places.\n"
        "- Use one distinctive trait per place, chosen from category, operation hours, indoor/outdoor, parking, description, or conditions.\n"
        "- If conditions are empty for many places, do not repeat 'no restrictions' for all of them; use another concrete trait instead.\n"
    )

    raw = await _chat_completion(
        _PLACE_REASON_SYSTEM_PROMPT,
        user_prompt,
        max_tokens=700,
    )

    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean)
        return {
            item["name"]: item["reason"]
            for item in data.get("places", [])
            if item.get("name") and item.get("reason")
        }
    except Exception as e:
        logger.warning(f"[ChatResponse] place reason parse failed: {e}")
        return {}


async def _is_out_of_service_area(query: str, request: Request | None = None) -> bool:
    """서울 외 지역 질문이면 True를 반환한다."""
    try:
        parsed = await _parse_query_with_llm(query, request=request)
        city = (parsed.objective.get("city") or "").strip()
        return bool(city and city != SEOUL)
    except Exception as e:
        logger.warning(f"[ChatResponse] service-area check failed: {e}")
        return False


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


async def _generate_diary_json(
    pet_ctx: dict,
    query: str,
    ctx: DispatchContext,
) -> str | None:
    """
        이미지 프롬프트 결정 → 이미지 생성(DiaryChain 우선) → S3 업로드 → images 테이블 저장.
        실패 시 None 반환.
    """
    # DiaryChain 경로는 image_prompt_final 포함, 없으면 build_final_image_prompt로 생성
    image_prompt: str = diary_data.get("image_prompt_final") or _diary_prompt_builder.build_final_image_prompt(
        image_prompt_base=diary_data.get("image_prompt_base", ""),
        breed=pet_ctx["breed"],
        breed_en=pet_ctx.get("breed_en"),
        birth_date=pet_ctx.get("birth_date"),
        personalities=pet_ctx.get("personalities", []),
        all_answers=[diary_data.get("_conversation", "")],
        emotion=diary_data.get("_emotion", _DEFAULT_DIARY_EMOTION),
    )

    # 1) 이미지 생성 — DiaryChain 우선, fallback: 직접 OpenAI 호출
    b64: str | None = None
    if _ai_container is not None:
        try:
            b64 = await _ai_container.diary_chain.generate_image(image_prompt_final=image_prompt)
        except Exception as e:
            logger.error(f"[Diary] DiaryChain.generate_image 실패, fallback: {e}")

    if b64 is None:
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
    diary_data = await _generate_diary_json(pet_ctx, query, user_id=ctx.user_id)

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
    if await _is_out_of_service_area(query, request=request):
        return _OUT_OF_SERVICE_AREA_MESSAGE

    if settings.USE_DUMMY_PLACES:
        places = await Place().find_place(top_k=top_k)
    elif ctx.db is not None:
        places = await search_places_from_db(query, ctx.db, n_results=top_k, request=request)
    else:
        logger.warning("[ChatResponse] db 세션 없음 — 장소 검색 불가")
        places = []

    if places:
        return _format_place_list_response(places)
    places_text = _format_places_brief(places)
    user_prompt = f"사용자 질문: {query}\n\n[검색된 장소]\n{places_text}"
    return await _chat_completion(_PLACES_SYSTEM_PROMPT, user_prompt)


async def _handle_facility(query: str, ctx: DispatchContext, request: Request = None) -> str:
    if await _is_out_of_service_area(query, request=request):
        return _OUT_OF_SERVICE_AREA_MESSAGE

    if settings.USE_DUMMY_PLACES:
        places = await Place().find_place(top_k=1)
    elif ctx.db is not None:
        places = await search_places_from_db(query, ctx.db, n_results=1, request=request)
    else:
        logger.warning("[ChatResponse] db 세션 없음 — 시설 검색 불가")
        places = []

    places_text = _format_places_brief(places)
    user_prompt = f"사용자 질문: {query}\n\n[검색된 시설]\n{places_text}"
    return await _chat_completion(_FACILITY_SYSTEM_PROMPT, user_prompt)


async def _handle_fallback(query: str) -> str:
    return await _chat_completion(_FALLBACK_SYSTEM_PROMPT, query)


async def dispatch(
    intent_result: IntentResult,
    query: str,
    ctx: DispatchContext | None = None,
    request: Request | None = None,
) -> str:
    """
    의도 분류 결과에 따라 적절한 핸들러로 라우팅하고 assistant 응답 텍스트를 반환합니다.
    """
    if ctx is None:
        ctx = DispatchContext()

    if is_diary_button_action(query):
        logger.info(f"[Dispatch] diary 버튼 액션 → diary_response_service: {query!r}")
        return await handle_diary_response(query, ctx)

    if is_diary_confirm_request(query):
        logger.info(f"[Dispatch] diary confirm 요청 → diary_response_service: {query!r}")
        return await handle_diary_response(query, ctx)

    intent = intent_result.intent
    logger.info(f"[ChatResponse] 의도: {intent}")
    top_k = int(intent_result.strategy.get("top_k", 5))

    if intent == "다이어리 작성":
        sub = detect_diary_sub_intent(query)
        logger.info(f"[ChatResponse] 다이어리 세부 의도: {sub}")
        if sub in {"guide_write", "guide_album", "guide_calendar"}:
            return get_diary_guide_response(sub)
        return await handle_diary_response(query, ctx)

    if intent == "장소추천":
        return await _handle_places(query, ctx, top_k=top_k, request=request)

    if intent == "시설정보":
        return await _handle_facility(query, ctx, request=request)
    if intent == "기타" or intent not in RAG_STRATEGY_MAP:
        logger.info("[Dispatch] 기타 분기 처리")
        return await _handle_fallback(query)

    logger.warning(f"[ChatResponse] 알 수 없는 의도: {intent} → fallback 처리")
    return await _handle_fallback(query)