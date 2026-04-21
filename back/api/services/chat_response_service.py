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


# ── AIContainer reference (set at startup by main.py) ────────────────────────
_ai_container = None


def set_ai_container(container) -> None:
    """앱 시작 시 main.py lifespan에서 호출해 AIContainer를 등록합니다."""
    global _ai_container
    _ai_container = container
    logger.info("[ChatResponse] AIContainer 등록 완료 — RAG 경로 활성화")


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


# 안내 응답에 붙이는 마커 — 프론트에서 [그림일기] 버튼 렌더링에 사용
_DIARY_BUTTON_MARKER = "##DIARY_BUTTON##"

# ── 안내 응답 (정적, GPT 호출 없음) ─────────────────────────────────────────
_RESPONSE_GUIDE_WRITE = (
    "그림일기는 두 가지 방법으로 쓸 수 있어요! ✍️\n\n"
    "**방법 1 · 버튼으로 시작하기**\n"
    "아래 [그림일기 시작하기] 버튼을 누르면 일기 유형 선택 → 질문 답변 → 감정 선택 순서로 "
    "단계별로 예쁜 일기를 만들 수 있어요 🐾\n\n"
    "**방법 2 · 대화로 바로 쓰기**\n"
    "오늘 있었던 일을 그냥 말씀해주세요.\n"
    "예) \"오늘 강아지랑 한강 공원 산책했어요\"\n"
    "→ 제가 몇 가지 여쭤보고 그림일기를 만들어드릴게요!\n\n"
    "오늘 어떤 하루를 보내셨나요?"
    + "\n" + _DIARY_BUTTON_MARKER
)

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


async def _generate_diary_json(
    pet_ctx: dict,
    query: str,
    user_id: int | None = None,
) -> dict | None:
    """DiaryChain (RAG 포함) 우선 → fallback: DiaryPromptBuilder 직접 호출."""
    emotion = _infer_emotion(query)
    diary_type = _infer_diary_type(query)
    conversation_summary = f"보호자: {query.strip()}"

    # ── RAG 경로: AIContainer.diary_chain 사용 ──────────────────────────────
    if _ai_container is not None:
        try:
            result = await _ai_container.diary_chain.run(
                pet_name=pet_ctx["pet_name"],
                breed=pet_ctx["breed"],
                breed_en=pet_ctx.get("breed_en"),
                birth_date=pet_ctx.get("birth_date"),
                personalities=pet_ctx.get("personalities", []),
                owner_name=pet_ctx.get("owner_name", ""),
                diary_type=diary_type,
                emotion=emotion,
                conversation_summary=conversation_summary,
                user_id=str(user_id or ""),
            )
            if result.get("title"):
                result["_emotion"] = emotion
                result["_diary_type"] = diary_type
                result["_conversation"] = conversation_summary
                logger.info(
                    "[Diary] DiaryChain(RAG) 생성 완료 — "
                    f"has_past_diaries={result.get('has_past_diaries')}"
                )
                return result
            logger.warning("[Diary] DiaryChain 결과 비어있음 — fallback 경로 사용")
        except Exception as e:
            logger.error(f"[Diary] DiaryChain 호출 실패, fallback으로 전환: {e}")

    # ── Fallback: DiaryPromptBuilder 직접 호출 (RAG 없음) ───────────────────
    prompt = _diary_prompt_builder.build_diary_prompt(
        pet_name=pet_ctx["pet_name"],
        breed=pet_ctx["breed"],
        birth_date=pet_ctx.get("birth_date"),
        personalities=pet_ctx.get("personalities", []),
        owner_name=pet_ctx.get("owner_name", ""),
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
        logger.error(f"[Diary] fallback 일기 생성/파싱 실패: {e}")
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


# ── 미니 플로우 상수 ──────────────────────────────────────────────────────────
_PICTURE_DIARY_PROPOSAL = "그림일기로 만들어드릴까요?"  # 생성 제안 감지 마커

_PICTURE_DIARY_YES = [
    "응", "네", "예", "ㅇㅇ", "ㅇ", "그래", "좋아", "좋아요", "ok", "OK",
    "만들어줘", "만들어주세요", "생성해줘", "생성해주세요", "그림일기 만들어줘",
]

_PICTURE_DIARY_NO = [
    "아니", "아니요", "괜찮아", "안해도돼", "안 해도 돼", "노", "no", "NO",
    "필요없어", "필요 없어", "됐어", "그냥 둬",
]

_MINI_FLOW_SYSTEM_PROMPT = """\
[역할]
- 너는 반려견 일기 작성 챗봇이다.
- 사용자의 말을 공감하며 듣고, 오늘의 핵심 사건과 감정을 정리해 일기 형식으로 작성한다.
- 사용자의 입력이 모호하면 필요한 정보만 최소한으로 질문한다.
- 정보가 충분하면 더 묻지 말고 바로 일기를 작성한다.

[대화 목표]
사용자의 자유 입력에서 아래 정보를 파악한다.
- 반려견 정보: 견종, 나이 (없으면 생략 가능)
- 오늘의 상황: 어디서 무엇을 했는지
- 핵심 사건: 오늘 가장 기억에 남는 장면
- 감정: 반려견의 감정 / 보호자의 감정
- 분위기: 밝음, 포근함, 신남, 잔잔함, 아쉬움 등

[대화 원칙]
1. 사용자가 처음부터 충분한 정보를 주면 추가 질문 없이 바로 일기를 작성한다.
2. 정보가 부족하면 한 번에 너무 많이 묻지 말고, 가장 필요한 것만 1~2개 질문한다.
3. 추가 질문은 자연스럽고 짧게 한다.
4. 없는 사실을 과하게 지어내지 않는다.
5. 다만 문장이 어색하지 않도록 최소한의 자연스러운 연결은 가능하다.
6. 사용자의 말투를 지나치게 따라 하지 말고, 서비스용으로 깔끔하고 따뜻한 문장으로 정리한다.
7. 유치하거나 과하게 오글거리는 표현은 피한다.
8. 일기는 짧고 읽기 좋게 작성한다.
9. 같은 표현을 반복하지 않는다.
10. 보호자와 반려견의 하루가 잘 느껴지도록 작성한다.

[추가 질문이 필요한 기준]
아래 중 하나라도 부족하면 질문할 수 있다.
- 오늘 무엇을 했는지 전혀 없음
- 어디서 있었는지 너무 불명확함
- 기억에 남는 장면이 없음
- 감정이나 분위기가 전혀 드러나지 않음

하지만 아래 중 2개 이상이 이미 있으면 웬만하면 바로 작성한다.
- 활동(산책, 놀기, 쉬기, 병원, 외출 등)
- 장소(공원, 집, 카페, 산책길 등)
- 감정(즐거움, 편안함, 아쉬움, 뿌듯함 등)
- 핵심 사건(뛰어놀았다, 친구를 만났다, 비를 피했다, 안겨 있었다 등)

[추가 질문 스타일]
좋은 예시:
- 오늘 가장 기억에 남는 장면이 뭐였나요?
- 집에서 놀았을 때 어떤 모습이 제일 귀여웠나요?
- 산책하면서 특별했던 일이 있었나요?
- 오늘 아이 기분은 어땠던 것 같나요?

나쁜 예시:
- 장소, 활동, 감정, 핵심 사건을 입력해주세요.
- 정보를 더 자세히 주세요.
- 일기 생성을 위해 데이터가 부족합니다.

[일기 작성 규칙]
- 3~5문장 정도로 작성한다.
- 한 편의 짧은 일기처럼 자연스럽게 이어지게 쓴다.
- 오늘의 핵심 사건이 중심이 되게 쓴다.
- 감정이 은은하게 드러나게 쓴다.
- 반려견의 행동이 눈에 그려지도록 쓰되 과장하지 않는다.
- 너무 설명문처럼 쓰지 말고 일기처럼 쓴다.
- "~했다", "~했다"만 반복되지 않게 문장을 다듬는다.
- 견종, 나이 정보가 있으면 자연스럽게 반영한다.
- 정보가 없으면 억지로 넣지 않는다.

[문체 가이드]
- 따뜻하고 담백한 문체
- 과한 의인화 금지
- 과한 감탄사 남발 금지
- 너무 슬랭스럽지 않게
- 서비스에서 바로 보여줄 수 있을 정도로 정돈된 문장

[출력 규칙]
상황에 따라 아래 두 가지 중 하나로만 응답한다.

1. 정보가 아직 부족한 경우
- 추가 질문만 짧게 한다.
- 일기는 아직 쓰지 않는다.

2. 정보가 충분한 경우
반드시 아래 형식으로만 출력한다.

{
  "mode": "final",
  "title": "일기 제목",
  "diary_text": "완성된 일기 본문"
}

주의:
- 정보가 부족한데 억지로 final을 출력하지 않는다.
- final일 때는 explanation, commentary, analysis 같은 불필요한 문구를 절대 넣지 않는다.
- title은 짧고 자연스럽게 작성한다.
- diary_text는 줄글 1단락으로 작성한다.\
"""


def _last_bot_proposed_picture_diary(history: list) -> bool:
    """마지막 어시스턴트 메시지가 그림일기 제안을 포함하는지 확인."""
    for m in reversed(history):
        if m.role == "assistant":
            return _PICTURE_DIARY_PROPOSAL in m.content
    return False


def _history_has_generated_diary(history: list) -> bool:
    """히스토리 내 봇 메시지에 이미 생성된 텍스트 일기가 있는지 확인."""
    return any(
        m.role == "assistant" and "📖 **" in m.content
        for m in history
    )


def _extract_all_user_content(messages: list) -> str:
    """전체 유저 메시지를 합쳐 일기 생성 소스로 사용."""
    return " ".join(m.content for m in messages if m.role == "user")


def _try_parse_final_diary(raw: str) -> dict | None:
    """GPT 응답에서 mode=final JSON을 추출. 실패 시 None.

    GPT가 JSON 앞뒤에 설명 문구를 붙이거나 마크다운 코드블록으로 감싸는 경우도 처리.
    """
    import re
    candidates = []

    # 1순위: ```json ... ``` 블록
    for m in re.finditer(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL):
        candidates.append(m.group(1))

    # 2순위: 텍스트 내 { ... } 블록 전체 (중첩 없는 단순 매칭)
    for m in re.finditer(r"\{[^{}]*\}", raw, re.DOTALL):
        candidates.append(m.group(0))

    for candidate in candidates:
        try:
            data = json.loads(candidate.strip())
            if isinstance(data, dict) and data.get("mode") == "final":
                return data
        except Exception:
            continue
    return None


async def _run_mini_flow_gpt(query: str, history: list, proposed_picture: bool = False) -> str:
    """대화 히스토리 + 현재 메시지를 새 시스템 프롬프트로 GPT에 전달."""
    system = _MINI_FLOW_SYSTEM_PROMPT
    if proposed_picture:
        system += (
            "\n\n[현재 상태]\n"
            "앞서 일기 초안을 제시하고 그림일기 생성 여부를 물었다. "
            "사용자가 명확히 yes/no를 하지 않고 추가 내용을 말했을 수 있다. "
            "추가 내용이 있으면 반영해 일기를 다시 작성하고 final JSON으로 출력하라. "
            "명확한 거절이면 질문 없이 짧게 마무리하라."
        )
    elif _history_has_generated_diary(history):
        system += (
            "\n\n[현재 상태]\n"
            "이미 텍스트 일기 초안이 생성된 상태다. "
            "사용자가 수정이나 보완을 요청했을 수 있다. "
            "수정 요청이면 히스토리의 기존 일기 내용을 바탕으로 반영해 다시 작성하고 final JSON으로 출력하라. "
            "새로운 내용 추가라면 합산해서 다시 작성하라."
        )
    messages: list[dict] = [{"role": "system", "content": system}]
    for m in history[-12:]:
        role = "user" if m.role == "user" else "assistant"
        messages.append({"role": role, "content": m.content})
    messages.append({"role": "user", "content": query})

    client = _get_openai_client()
    response = await client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages,
        max_tokens=600,
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()


async def _handle_diary_mini_flow(query: str, ctx: DispatchContext) -> str:
    """
    대화 기반 일기 작성 미니 플로우.

    흐름:
      - GPT가 정보 부족 → 자연스러운 추가 질문 반환
      - GPT가 정보 충분 → JSON {"mode":"final","title":...,"diary_text":...} 반환
        → 일기 텍스트 포맷 후 그림일기 제안 질문 추가
      - 마지막 봇 메시지가 그림일기 제안이었을 때:
          사용자 yes → _handle_diary() (RAG + 이미지 생성)
          사용자 no  → 더 이야기할 내용 있으면 말씀해달라 안내
    """
    history = []
    if ctx.db is not None and ctx.room_id is not None:
        try:
            from services.chat_message_service import list_messages
            history = list(await list_messages(ctx.room_id, ctx.db, last_n=20))
        except Exception as e:
            logger.warning(f"[DiaryMiniFlow] 히스토리 조회 실패: {e}")

    q = query.strip()

    # ① 마지막 봇 메시지가 그림일기 제안이었으면 yes/no 처리
    if _last_bot_proposed_picture_diary(history):
        # 짧은 단독 응답일 때만 yes/no로 해석 (긴 문장은 일기 추가 내용으로 간주)
        if len(q) <= 20 and any(t in q for t in _PICTURE_DIARY_YES):
            combined = _extract_all_user_content(history) or query
            logger.info("[DiaryMiniFlow] 그림일기 승인 → 전체 대화로 일기 생성")
            return await _handle_diary(combined, ctx)
        if len(q) <= 20 and any(t in q for t in _PICTURE_DIARY_NO):
            return "알겠어요! 수정하거나 추가하고 싶은 내용이 있으면 말씀해 주세요. 반영해서 다시 써드릴게요. 😊"
        # 애매하거나 긴 응답 → GPT에게 맡김 (추가 내용으로 처리)

    # ② GPT로 대화 처리 (정보 충분하면 final JSON, 부족하면 추가 질문)
    proposed = _last_bot_proposed_picture_diary(history)
    try:
        raw = await _run_mini_flow_gpt(query, history, proposed_picture=proposed)
    except Exception as e:
        logger.error(f"[DiaryMiniFlow] GPT 호출 실패: {e}")
        return "죄송해요, 잠시 문제가 생겼어요. 다시 시도해주세요."

    # ③ final JSON 파싱
    final = _try_parse_final_diary(raw)
    if final:
        title = final.get("title", "오늘의 일기")
        diary_text = final.get("diary_text", "")
        logger.info("[DiaryMiniFlow] final JSON 수신 → 일기 포맷 후 그림일기 제안")
        return (
            f"📖 **{title}**\n\n"
            f"{diary_text}\n\n"
            f"---\n{_PICTURE_DIARY_PROPOSAL} 🎨\n"
            "원하시면 '응' 또는 '만들어줘'라고 말씀해주세요!"
        )

    # ④ 추가 질문 그대로 반환
    return raw


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
