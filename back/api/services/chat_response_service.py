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

import json
import logging

from dataclasses import dataclass
from typing import Sequence

from fastapi import Request
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.location.place import Place
from models.pet import Pet
from models.user import User
from services.intent_service import IntentResult, RAG_STRATEGY_MAP
from services.place_service import (
    ParsedQuery,
    SEOUL,
    _parse_query_with_llm,
    search_facility_by_name,
    search_places_from_db,
)
from services.place_image_service import enrich_place_images

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
_OUT_OF_SERVICE_AREA_MESSAGE = "현재 서비스는 서울 지역만 지원하고 있습니다."
_PLACE_NOT_FOUND_MESSAGE = "조건에 맞는 장소를 찾지 못했어요."


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
    pet_id: int | None = None
    user_lat: float | None = None
    user_lng: float | None = None


@dataclass
class DispatchResult:
    """
        dispatch 결과 컨테이너.

        - text: 챗봇 응답 본문 (assistant 메시지 content 로 저장됨)
        - facility: 시설정보 의도일 때 단일 시설 카드 페이로드 (그 외 None)
        - places: 장소추천 의도일 때 장소 카드 페이로드 (그 외 None)
    """
    text: str
    facility: dict | None = None
    places: list[dict] | None = None


_PLACES_SYSTEM_PROMPT = (
    "너는 반려견 동반 가능 장소를 추천하는 큐레이터야. "
    "검색된 장소 목록을 참고해 사용자에게 자연스러운 한국어로 2~3곳을 추천하되 "
    "각 장소의 특징(카테고리/위치/실내외 여부 등)을 간결하게 곁들여줘. "
    "만약 '[검색 결과 없음]'이 표시되면, 조건에 맞는 장소를 찾지 못했다고 안내하고 "
    "현재 서비스는 서울 지역만 지원하므로 다른 지역 요청인 경우 그 점을 친절하게 알려줘."
    "데이터에 없는 운영 정책·시설 정보 (목줄 의무, 입장료, 영업 시간, 반려동물 정책 등)를 추측해서 답하지 말 것"
    "모르는 정보는 '확인이 필요한 정보' 로 안내하고, 사용자가 직접 확인하도록 유도"
    "조건 완화 제안 시에도 사실로 보이는 부가 도메인 지식을 끼워 넣지 말 것"
)

_FACILITY_SYSTEM_PROMPT = (
    "너는 반려견 동반 가능 시설의 상세 정보를 안내하는 챗봇이야. "
    "검색된 시설 한 곳의 정보를 바탕으로 운영시간·주소·주차·이용조건을 사용자가 이해하기 쉽게 설명해."
)

# 시설정보 의도가 묻는 속성 슬롯 — 답변 필드 선택에 사용
_FACILITY_SLOT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "operation":      ("운영", "영업", "오픈", "열려", "몇시", "몇 시", "휴무", "쉬는날",
                       "쉬는 날", "마감", "주말", "평일", "공휴일", "연중무휴", "24시간"),
    "parking":        ("주차",),
    "fee":            ("입장료", "이용료", "요금", "비용", "추가요금", "추가 요금",
                       "유료", "무료", "가격", "돈"),
    "conditions":     ("조건", "제한", "목줄", "배변", "리드줄", "케이지", "안고", "동반"),
    "location":       ("주소", "위치", "어디", "찾아가", "오시는길", "오는길"),
    "contact":        ("전화", "연락처", "번호"),
    "indoor_outdoor": ("실내", "실외", "야외", "테라스"),
}

_FACILITY_FIELD_LABELS: dict[str, str] = {
    "operation":      "운영시간",
    "parking":        "주차",
    "fee":            "이용 요금",
    "conditions":     "반려견 동반 조건",
    "location":       "주소",
    "contact":        "전화",
    "indoor_outdoor": "실내/실외",
}

_FACILITY_NOT_FOUND_MESSAGE = (
    "찾으시는 시설을 정확히 파악하지 못했어요.\n"
    "시설 이름을 조금 더 구체적으로 알려주시면 자세히 안내해 드릴게요.\n"
    "예) \"○○카페 운영시간 알려줘\", \"△△공원 주차 가능해?\""
)


def _detect_facility_slots(query: str) -> list[str]:
    """질문에서 어떤 속성을 묻는지 키워드 기반으로 추출. 매칭 0개면 기본 6필드 노출."""
    text = query or ""
    matched: list[str] = []
    for slot, keywords in _FACILITY_SLOT_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            matched.append(slot)
    return matched


def _facility_field_value(facility: dict, slot: str) -> str | None:
    """슬롯에 해당하는 표시용 문자열을 반환. 데이터가 비어있으면 None."""
    if slot == "operation":
        raw = (facility.get("operation") or "").strip()
        if not raw:
            return None
        for prefix in ("운영시간:", "운영시간："):
            if raw.startswith(prefix):
                raw = raw[len(prefix):].lstrip()
                break
        return raw or None

    if slot == "parking":
        v = (facility.get("has_parking") or "").strip()
        if v == "Y":
            return "주차 가능"
        if v == "N":
            return "주차 불가"
        return None

    if slot == "fee":
        ent_amount = facility.get("entrance_fee_amount")
        ext_amount = facility.get("extra_fee_amount")
        ent_type = facility.get("entrance_fee_type") or "unknown"
        ext_type = facility.get("extra_fee_type") or "unknown"
        parts: list[str] = []
        if ent_type == "free":
            parts.append("입장료 무료")
        elif ent_type == "fixed" and ent_amount:
            parts.append(f"입장료 {int(ent_amount):,}원")
        elif ent_type in {"variable", "conditional"}:
            parts.append("입장료 변동/조건부")
        if ext_type == "free":
            parts.append("강아지 추가요금 없음")
        elif ext_type == "fixed" and ext_amount:
            parts.append(f"강아지 추가요금 {int(ext_amount):,}원")
        elif ext_type in {"variable", "conditional"}:
            parts.append("강아지 추가요금 변동/조건부")
        return " · ".join(parts) if parts else None

    if slot == "conditions":
        return (facility.get("conditions") or "").strip() or None

    if slot == "location":
        return (facility.get("address") or "").strip() or None

    if slot == "contact":
        return (facility.get("tel") or "").strip() or None

    if slot == "indoor_outdoor":
        indoor = facility.get("indoor") == "Y"
        outdoor = facility.get("outdoor") == "Y"
        if indoor and outdoor:
            return "실내·실외 모두 이용 가능"
        if indoor:
            return "실내 이용 가능"
        if outdoor:
            return "실외 이용 가능"
        return None

    return None


def _format_facility_response(facility: dict, slots: list[str]) -> str:
    """검색된 시설을 바탕으로 결정적(LLM 미사용) 답변 텍스트를 생성한다.

    7개 핵심 필드(운영시간·주차·이용 요금·반려견 동반 조건·주소·전화·실내/실외)를
    **항상 모두** 노출한다. 데이터가 없는 항목은 '정보 없음'으로 명시하여
    hallucinate 위험을 차단한다.

    슬롯(`slots`)이 매칭됐으면 해당 필드를 **맨 위로 정렬**하여 강조하고,
    매칭이 없으면 `_FACILITY_FIELD_LABELS` 정의 순서대로 노출한다. 슬롯은
    필드 숨김 용도가 아니다.
    """
    name = facility.get("name") or "시설"
    lines: list[str] = [f"📍 **{name}**"]

    base_order = list(_FACILITY_FIELD_LABELS.keys())
    if slots:
        priority = [s for s in slots if s in _FACILITY_FIELD_LABELS]
        rest = [s for s in base_order if s not in priority]
        target_slots = priority + rest
    else:
        target_slots = base_order

    for slot in target_slots:
        label = _FACILITY_FIELD_LABELS.get(slot)
        if not label:
            continue
        value = _facility_field_value(facility, slot)
        if value:
            lines.append(f"- {label}: {value}")
        else:
            lines.append(f"- {label}: 정보 없음")

    lines.append("")
    lines.append("좌측 지도와 시설 카드에서 위치를 함께 확인해보세요.")
    return "\n".join(lines)

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
        return _PLACE_NOT_FOUND_MESSAGE

    lines = ["반려견과 함께 가보기 좋은 장소를 정리했어요.", ""]
    for idx, place in enumerate(places, start=1):
        name = place.get("name", "이름 미상")
        address = place.get("address", "")
        reason = (place.get("reason") or "").strip()
        content_id = (place.get("content_id") or "").strip()

        lines.append(f"{idx}. {name}")
        lines.append("")
        if address:
            lines.append(f"- 주소: {address}")
            lines.append("")
        if reason:
            lines.append(f"- 추천 이유: {reason}")
            lines.append("")
        if content_id:
            lines.append(f"- _id: {content_id}")
            lines.append("")

    lines.append("세부 정보는 좌측 지도와 장소 카드에서 함께 확인해보세요.")
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


async def _is_out_of_service_area(
    query: str,
    request: Request | None = None,
    parsed: ParsedQuery | None = None,
) -> bool:
    """서울 외 지역 질문이면 True를 반환한다."""
    try:
        parsed = parsed or await _parse_query_with_llm(query, request=request)
        city = (parsed.objective.get("city") or "").strip()
        return bool(city and city != SEOUL)
    except Exception as e:
        logger.warning(f"[ChatResponse] service-area check failed: {e}")
        return False


async def _load_place_preference_context(ctx: DispatchContext) -> dict:
    """Load the current user's profile tags for place recommendation reranking."""
    if ctx.db is None or (ctx.user_id is None and ctx.pet_id is None):
        return {"pet_name": "", "dog_tags": [], "owner_tags": []}

    pet_name = ""
    dog_tags: list[str] = []
    owner_tags: list[str] = []
    owner_user_id = ctx.user_id

    try:
        pet_query = select(Pet).where(Pet.deleted_at.is_(None))
        if ctx.pet_id is not None:
            pet_query = pet_query.where(Pet.id == ctx.pet_id).limit(1)
        elif ctx.user_id is not None:
            pet_query = (
                pet_query.where(Pet.user_id == ctx.user_id)
                .order_by(Pet.id.desc())
                .limit(1)
            )
        else:
            pet_query = pet_query.limit(0)

        pet_result = await ctx.db.execute(pet_query)
        pet = pet_result.scalar_one_or_none()
        if pet is not None:
            pet_name = pet.name or ""
            dog_tags = list(pet.selected_tags or [])
            owner_user_id = pet.user_id
    except Exception as e:
        logger.warning(f"[ChatResponse] pet preference load failed: {e}")

    if owner_user_id is not None:
        try:
            user_result = await ctx.db.execute(
                select(User).where(User.id == owner_user_id, User.deleted_at.is_(None))
            )
            user = user_result.scalar_one_or_none()
            if user is not None:
                owner_tags = list(user.selected_tags or [])
        except Exception as e:
            logger.warning(f"[ChatResponse] user preference load failed: {e}")

    profile_ctx = {
        "pet_name": pet_name,
        "dog_tags": dog_tags,
        "owner_tags": owner_tags,
    }
    logger.info(
        "[ChatResponse] place profile loaded | user_id=%s | pet_name=%s | dog_tags=%s | owner_tags=%s",
        owner_user_id,
        pet_name,
        dog_tags,
        owner_tags,
    )
    return profile_ctx


def _rerank_places_with_profile(
    places: list[dict],
    profile_ctx: dict,
    request: Request | None = None,
) -> list[dict]:
    """Apply PlacesChain reranking rules to already-fetched place results."""
    if not places:
        return places

    dog_tags = profile_ctx.get("dog_tags") or []
    owner_tags = profile_ctx.get("owner_tags") or []
    if not (dog_tags or owner_tags):
        logger.info("[ChatResponse] profile rerank skipped | no dog/owner tags")
        return places

    try:
        container = request.app.state.ai_container if request else None
        places_chain = getattr(container, "places_chain", None) if container else None
        if places_chain is None:
            logger.info("[ChatResponse] profile rerank skipped | places_chain unavailable")
            return places
        return places_chain.rerank_places(
            places,
            dog_tags=dog_tags,
            owner_tags=owner_tags,
        )
    except Exception as e:
        logger.warning(f"[ChatResponse] profile rerank failed: {e}")
        return places

# ── 의도별 핸들러 ────────────────────────────────────────────────────────────
async def _handle_places(
    query: str,
    ctx: DispatchContext,
    top_k: int = 5,
    request: Request = None,
) -> tuple[str, list[dict]]:
    parsed = await _parse_query_with_llm(query, request=request)
    if await _is_out_of_service_area(query, request=request, parsed=parsed):
        return _OUT_OF_SERVICE_AREA_MESSAGE, []

    profile_ctx = await _load_place_preference_context(ctx)

    if settings.USE_DUMMY_PLACES:
        places = await Place().find_place(top_k=top_k)
    elif ctx.db is not None:
        places = await search_places_from_db(
            query,
            ctx.db,
            n_results=top_k,
            request=request,
            user_lat=ctx.user_lat,
            user_lng=ctx.user_lng,
            pre_parsed=parsed,
        )
    else:
        logger.warning("[ChatResponse] db 세션 없음 — 장소 검색 불가")
        places = []

    places = _rerank_places_with_profile(places, profile_ctx, request=request)

    if places:
        places = await enrich_place_images(places)
        reasons = await generate_place_reasons(query, places)
        for place in places:
            place["reason"] = reasons.get(place.get("name", ""), "")
        return _format_place_list_response(places), places

    return _PLACE_NOT_FOUND_MESSAGE, []


async def _handle_facility(
    query: str,
    ctx: DispatchContext,
    request: Request | None = None,
) -> tuple[str, dict | None]:
    """
        시설정보 의도 핸들러 — 단일 시설을 정확히 찾아 결정적 답변 + 카드 페이로드 반환.

        장소추천과 달리 LLM 답변 생성을 사용하지 않는다. 데이터에 있는 필드만
        고정 형식으로 노출하여 hallucinate 위험을 제거한다.

        Returns:
                (text, facility_dict)
                - facility 매칭 실패: ("못 찾음 안내", None)
                - 서비스 외 지역  : (안내, None)
                - 정상 매칭        : (필드 요약 텍스트, search_facility_by_name 결과 dict)
    """
    if ctx.db is None:
        logger.warning("[ChatResponse] db 세션 없음 — 시설 검색 불가")
        return _FACILITY_NOT_FOUND_MESSAGE, None

    result = await search_facility_by_name(query, ctx.db, request=request)
    if result.out_of_service_area:
        return _OUT_OF_SERVICE_AREA_MESSAGE, None
    if result.facility is None:
        return _FACILITY_NOT_FOUND_MESSAGE, None

    facility = result.facility
    slots = _detect_facility_slots(query)
    text = _format_facility_response(facility, slots)
    logger.info(
        f"[FacilityHandler] facility={facility.get('name')!r} "
        f"slots={slots} confidence={facility.get('match_confidence')}"
    )
    return text, facility


async def _handle_fallback(query: str) -> str:
    return await _chat_completion(_FALLBACK_SYSTEM_PROMPT, query)


async def dispatch(
    intent_result: IntentResult,
    query: str,
    ctx: DispatchContext | None = None,
    request: Request | None = None,
) -> DispatchResult:
    """
    의도 분류 결과에 따라 적절한 핸들러로 라우팅하고 응답을 반환합니다.

    반환은 항상 `DispatchResult` 로 감싸지며, 시설정보 의도일 때만
    `facility` 필드에 카드 페이로드가 채워집니다 (그 외 None).
    """
    if ctx is None:
        ctx = DispatchContext()

    if is_diary_button_action(query):
        logger.info(f"[Dispatch] diary 버튼 액션 → diary_response_service: {query!r}")
        return DispatchResult(text=await handle_diary_response(query, ctx))

    if is_diary_confirm_request(query):
        logger.info(f"[Dispatch] diary confirm 요청 → diary_response_service: {query!r}")
        return DispatchResult(text=await handle_diary_response(query, ctx))

    intent = intent_result.intent
    logger.info(f"[ChatResponse] 의도: {intent}")
    top_k = int(intent_result.strategy.get("top_k", 5))

    if intent == "다이어리 작성":
        sub = detect_diary_sub_intent(query)
        logger.info(f"[ChatResponse] 다이어리 세부 의도: {sub}")
        if sub in {"guide_write", "guide_album", "guide_calendar"}:
            return DispatchResult(text=get_diary_guide_response(sub))
        return DispatchResult(text=await handle_diary_response(query, ctx))

    if intent == "장소추천":
        text, places = await _handle_places(query, ctx, top_k=top_k, request=request)
        return DispatchResult(text=text, places=places)

    if intent == "시설정보":
        text, facility = await _handle_facility(query, ctx, request=request)
        return DispatchResult(text=text, facility=facility)

    if intent == "기타" or intent not in RAG_STRATEGY_MAP:
        logger.info("[Dispatch] 기타 분기 처리")
        return DispatchResult(text=await _handle_fallback(query))

    logger.warning(f"[ChatResponse] 알 수 없는 의도: {intent} → fallback 처리")
    return DispatchResult(text=await _handle_fallback(query))
