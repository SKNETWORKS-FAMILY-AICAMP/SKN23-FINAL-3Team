# -*- coding: utf-8 -*-
"""
services/diary_response_service.py
----------------------------------
자유채팅 기반 다이어리 응답 전용 서비스.

역할:
- 다이어리 의도 세부 분류
- 자유채팅 다이어리 미니 플로우
- follow-up / confirm / 버튼 액션 처리
- 텍스트 일기 생성 / 그림일기 생성
"""

from __future__ import annotations

import json
import base64
import logging
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Literal

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from openai import AsyncOpenAI

from models.pet import Pet
from models.image import Image
from models.user import User
from core.config import settings
from services.image_service import _upload_to_s3
from ai.prompts.diary_prompt_builder import DiaryPromptBuilder

from services.diary_service import create_diary
from schemas.diary import DiaryCreate

logger = logging.getLogger(__name__)

_diary_prompt_builder = DiaryPromptBuilder()

_openai_client: AsyncOpenAI | None = None
_GPT_MODEL = settings.GPT_MODEL
_IMAGE_MODEL = settings.GPT_IMAGE_MODEL

_BUTTONS_MARKER = "%%BUTTONS%%"


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# ── 다이어리 의도 세부 키워드 분류 ──────────────────────────────────────────
# "처음" 같은 단독 키워드는 실제 일기 본문에 너무 자주 등장해서 guide_write 오분류를 유발하므로 제거
_GUIDE_WRITE_KEYWORDS = [
    "어떻게 써", "어떻게 쓰", "어떻게 만들", "일기 어떻게",
    "사용법", "가이드", "도움말", "how",
    "모르겠", "모르겠어", "모르는데", "어떡해야", "어떻게 해야",
    "일기 쓰는 법", "그림일기 쓰는 법", "일기 작성 방법", "그림일기 작성 방법",
]

_GUIDE_ALBUM_KEYWORDS = [
    "앨범", "모아보기", "저장된", "쓴 일기", "다 쓴", "완성된", "기록",
    "어디서 봐", "어디에서 봐", "어디서 볼", "볼 수 있", "어디 있",
    "어디서 확인", "어디에서 확인", "찾을 수", "보관",
]

_GUIDE_CALENDAR_KEYWORDS = [
    "캘린더", "달력", "날짜별", "월별", "날짜로",
]

_FOLLOW_UP_MARKERS = [
    "더 이야기해주시면", "어디에 갔나요", "조금 더 알려주시면",
    "무슨 일이 있었나요", "특별히 기억에 남는",
    "가장 기억에 남는 순간", "한두 문장만 더 알려주세요",
    "조금 더 이야기해주세요", "어떤 감정이었나요", "어떤 순간이 가장",
    "어떤 부분을 수정할까요",
]

_DIARY_WRITE_REQUEST_PATTERNS: tuple[str, ...] = (
    "일기써줘", "일기써주세요", "일기작성해줘", "일기작성해주세요",
    "그림일기써줘", "그림일기만들어줘", "그림일기써", "그림일기만들어",
    "방금내용으로일기써줘", "방금내용으로일기",
    "이내용으로일기써줘", "이내용으로써줘", "이걸로일기써줘",
    "일기로정리해줘", "일기로기록해줘",
    "정리해줘", "기록해줘",
)

_DIARY_DIRECT_REQUEST_PATTERNS: tuple[str, ...] = (
    "바로써줘", "바로일기써줘", "그냥써줘", "그냥일기써줘",
    "바로만들어줘", "아니바로써줘", "아니일기바로써줘",
)

_DIARY_IMAGE_REQUEST_PATTERNS: tuple[str, ...] = (
    "그림일기로만들어줘", "그림일기완성하기", "그림일기생성", "그림생성", "이미지만들어줘", "그림만들어줘",
)

_DIARY_REVISE_REQUEST_PATTERNS: tuple[str, ...] = (
    "일기내용수정하기", "일기내용수정", "내용수정", "수정해줘", "수정할게",
    "일기다시쓰고싶어", "다시쓰고싶어", "다시써줘",
)

_DIARY_CONTINUE_PATTERNS: tuple[str, ...] = (
    "더이야기할래", "더이야기하고싶어", "더말할래", "더말하고싶어",
    "좀더이야기할래", "조금더이야기할래", "좀더말할래",
)

_DIARY_CREATE_PATTERNS: tuple[str, ...] = (
    "일기만들어줘", "일기만들어주세요",
)

_DIARY_CONFIRM_PATTERNS: tuple[str, ...] = (
    "응그렇게써줘", "그대로해줘", "좋아그렇게해줘", "응그렇게해줘",
    "그걸로해줘", "좋아그렇게작성해줘", "그렇게써줘", "그대로써줘",
    "오케이그렇게", "네그렇게", "응써줘", "그래써줘",
    "그냥그대로", "그대로작성해줘", "그대로출력해줘",
    "응맞아", "좋아써줘", "그렇게해줘", "그래그렇게",
)

_DIARY_REASSERT_PATTERNS: tuple[str, ...] = (
    "아니일기를써달라고",
    "아니일기써달라고",
    "일기써달라고",
    "일기써달라니까",
    "일기써달라고했잖아",
    "내말로일기써줘",
    "방금내용으로일기써달라고",
    "그얘기로일기써줘",
)

_FOLLOWUP_DIARY_REF_PATTERNS: tuple[str, ...] = (
    "이거로일기", "이걸로일기", "이내용으로일기",
    "방금말한걸로일기", "방금한말로일기", "방금내용으로일기",
    "그걸로일기", "그내용으로일기", "그거로일기",
    "이거로그림일기", "이걸로그림일기", "그걸로그림일기",
    "방금말한걸로그림일기", "방금내용으로그림일기",
    "일기로만들어줘", "일기써줄래", "일기만들어줄래",
    "일기쓰자", "그림일기쓰자",
)

_FOLLOWUP_DIARY_STANDALONE: frozenset[str] = frozenset({
    "일기", "그림일기", "일기요", "그림일기요", "일기쓰자", "일기써",
})

# 내용 없는 순수 시작 요청 — 프론트엔드 다이어리 플로우를 직접 트리거
_DIARY_START_FLOW_EXACT: frozenset[str] = frozenset({
    "일기써줘", "일기써주세요", "일기쓸래", "일기쓸래요",
    "일기쓰고싶어", "일기쓰고싶어요", "일기쓰자", "일기쓸게", "일기쓸게요",
    "그림일기써줘", "그림일기써주세요", "그림일기쓸래", "그림일기쓸래요",
    "그림일기쓰고싶어", "그림일기쓰고싶어요", "그림일기쓰자",
    "그림일기쓸게", "그림일기쓸게요",
})

# 프론트엔드로 보내는 특수 트리거 마커
_DIARY_FLOW_TRIGGER = "%%TRIGGER:START_DIARY%%"

# ── 인젝션 / 탈옥 사전 차단 ────────────────────────────────────────────────
# 한국어: "이전 지시" 단독이면 "이전 지시한 산책 코스" 같은 정상 문장도 차단되므로
# "이전 지시 무시", "이전 지시를 무시" 등 공격 의도가 명확한 구문만 등록.
# "역할을 바꿔" → "역할을 바꿔줘" / "역할을 바꿔서"는 정상이므로 "바꿔줘"로 한정.
_INJECTION_KEYWORDS_KO: tuple[str, ...] = (
    "이전 지시를 무시", "이전 지시 무시", "이전 지시는 무시",
    "프롬프트 무시", "프롬프트를 무시",
    "시스템 프롬프트",
    "지금부터 너는",
    "역할을 바꿔줘", "역할 변경해줘", "역할을 변경해",
    "다른 캐릭터로", "다른 캐릭터야",
    "탈옥",
    "롤플레이 시작",
)
# 영어: "bypass", "disregard" 단독은 정상 문맥에서도 등장 가능하므로 구문 단위로 한정.
_INJECTION_KEYWORDS_EN: tuple[str, ...] = (
    "ignore previous", "ignore all instructions", "ignore above",
    "system prompt", "you are now",
    "developer mode", "jailbreak",
    "override instructions",
    "disregard all", "disregard previous",
)
_INJECTION_RESPONSE = (
    "일기 작성과 관련 없는 요청이에요. "
    "오늘 반려견과 있었던 일을 알려주시면 일기를 써드릴게요! 🐾"
)


def _contains_injection(text: str) -> bool:
    """인젝션/탈옥 키워드가 포함되어 있는지 검사."""
    normalized = text.lower().replace(" ", "")
    for kw in _INJECTION_KEYWORDS_KO:
        if kw.replace(" ", "") in normalized:
            return True
    lower_en = text.lower()
    for kw in _INJECTION_KEYWORDS_EN:
        if kw in lower_en:
            return True
    return False


_DIARY_EVENT_KEYWORDS: tuple[str, ...] = (
    "산책", "목욕", "병원", "입양", "처음", "만남", "여행", "외출", "공원",
    "카페", "갔어", "왔어", "했어", "놀았", "먹었", "잤어", "아팠",
    "데려", "만났", "방문", "나들이", "훈련", "수영", "이사", "새끼",
    "갔어요", "왔어요", "했어요", "토했", "토해", "토해서", "구토",
)

_DIARY_EMOTION_KEYWORDS: tuple[str, ...] = (
    "설레", "행복", "뿌듯", "무서", "걱정", "귀여", "좋아", "재미", "슬퍼",
    "기뻐", "신나", "감동", "그리워", "달달", "조마조마", "안도",
    "감사", "사랑", "포근", "따뜻", "흐뭇", "아련", "뭉클",
    "걱정됐", "안쓰러", "무서웠", "아팠", "괜찮아",
)

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

_DEFAULT_DIARY_PET = {
    "pet_name": "우리 아이",
    "breed": "강아지",
    "breed_en": None,
    "birth_date": None,
    "personalities": [],
    "owner_name": "",
    "pet_id": None,
}
_DEFAULT_DIARY_TYPE = "daily"
_DEFAULT_DIARY_EMOTION = "😊"

_EMOTION_CANDIDATES = ["😊", "😌", "🥹", "😴", "😟", "🤍"]

_DIARY_TYPE_KEYWORDS: dict[str, tuple[str, ...]] = {
    "memory": ("여행", "처음", "추억", "기념", "특별"),
    "owner": ("나랑", "함께", "같이", "우리", "교감", "포근"),
    "dog": ("간식", "산책", "공놀이", "뛰어", "짖", "병원", "토", "구토", "아파"),
    "daily": ("평범", "일상", "하루", "루틴"),
}


# ── 외부 공개용 함수 ────────────────────────────────────────────────────────
def is_diary_button_action(query: str) -> bool:
    return _is_any_button_action(query) or _is_diary_reassert_request(query)


def is_diary_confirm_request(query: str) -> bool:
    return _is_diary_confirm_request(query)


def is_diary_start_flow_request(query: str) -> bool:
    return _is_diary_start_flow_request(query)


def detect_diary_sub_intent(query: str) -> str:
    return _detect_diary_sub_intent(query)


def get_diary_guide_response(sub_intent: str) -> str:
    if sub_intent == "guide_write":
        return _RESPONSE_GUIDE_WRITE
    if sub_intent == "guide_album":
        return _RESPONSE_GUIDE_ALBUM
    if sub_intent == "guide_calendar":
        return _RESPONSE_GUIDE_CALENDAR
    return _RESPONSE_GUIDE_WRITE


async def handle_diary_response(query: str, ctx: Any) -> str:
    return await _handle_diary_mini_flow(query, ctx)


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────
def _is_explicit_diary_request(query: str) -> bool:
    normalized = query.replace(" ", "")
    if any(pat in normalized for pat in _DIARY_WRITE_REQUEST_PATTERNS):
        return True

    has_diary_word = ("일기" in query) or ("그림일기" in query)
    has_write_word = any(
        kw in query for kw in ["써", "작성", "정리", "기록", "만들어", "만들어줘"]
    )
    return has_diary_word and has_write_word


def _is_direct_diary_request(query: str) -> bool:
    normalized = query.replace(" ", "")
    return any(pat in normalized for pat in _DIARY_DIRECT_REQUEST_PATTERNS)


def _is_image_generation_request(query: str) -> bool:
    normalized = query.replace(" ", "")
    return any(pat in normalized for pat in _DIARY_IMAGE_REQUEST_PATTERNS)


def _is_diary_revision_request(query: str) -> bool:
    normalized = query.replace(" ", "")
    return any(pat in normalized for pat in _DIARY_REVISE_REQUEST_PATTERNS)


def _is_continue_chat_request(query: str) -> bool:
    normalized = query.replace(" ", "")
    return any(pat in normalized for pat in _DIARY_CONTINUE_PATTERNS)


def _is_diary_confirm_request(query: str) -> bool:
    normalized = query.replace(" ", "")
    return any(pat in normalized for pat in _DIARY_CONFIRM_PATTERNS)


def _is_diary_create_request(query: str) -> bool:
    normalized = query.replace(" ", "")
    return any(pat in normalized for pat in _DIARY_CREATE_PATTERNS)


def _is_diary_reassert_request(query: str) -> bool:
    normalized = query.replace(" ", "")
    return any(pat in normalized for pat in _DIARY_REASSERT_PATTERNS)


def _is_any_button_action(query: str) -> bool:
    return (
        _is_image_generation_request(query)
        or _is_diary_revision_request(query)
        or _is_continue_chat_request(query)
        or _is_diary_create_request(query)
    )


def _is_diary_draft_message(bot_content: str) -> bool:
    return (
        "마음에 드세요?" in bot_content
        and ("그림일기로 만들어줘" in bot_content or "그림일기 완성하기" in bot_content)
        and ("일기 다시 쓰고 싶어" in bot_content or "일기 내용 수정하기" in bot_content)
    )


def _is_diary_start_flow_request(query: str) -> bool:
    """내용 없이 '일기 써줘', '그림일기 쓸래' 등 순수 시작 요청인지 판단."""
    return query.replace(" ", "") in _DIARY_START_FLOW_EXACT


def _is_followup_diary_request(query: str) -> bool:
    normalized = query.replace(" ", "")
    if any(pat in normalized for pat in _FOLLOWUP_DIARY_REF_PATTERNS):
        return True
    return query.strip() in _FOLLOWUP_DIARY_STANDALONE


def _extract_meaningful_user_content(recent_messages: list, limit: int = 3) -> str:
    parts = []
    for m in recent_messages:
        if m.role != "user":
            continue
        content = (m.content or "").strip()
        if not content or len(content) < 5:
            continue
        if _is_any_button_action(content):
            continue
        if _is_explicit_diary_request(content):
            continue
        if _is_direct_diary_request(content):
            continue
        if _is_followup_diary_request(content):
            continue
        if _is_diary_reassert_request(content):
            continue
        parts.append(content)
    return " ".join(parts[-limit:])


def _strip_buttons(content: str) -> str:
    idx = content.find(_BUTTONS_MARKER)
    return content[:idx].strip() if idx != -1 else content


def _extract_draft_text(bot_content: str) -> str:
    draft = _strip_buttons(bot_content)
    cutoff_marker = "마음에 드세요?"
    ci = draft.find(cutoff_marker)
    if ci != -1:
        draft = draft[:ci].strip()
    return draft.strip()


def _collect_diary_context(recent_messages: list, owner_label: str = "보호자") -> str:
    lines = []
    for m in recent_messages:
        raw = (m.content or "").strip()
        content = _strip_buttons(raw)
        if not content:
            continue
        if m.role == "assistant":
            if any(marker in content for marker in _FOLLOW_UP_MARKERS):
                lines.append(f"봇: {content}")
        elif m.role == "user":
            if (
                not _is_explicit_diary_request(content)
                and not _is_direct_diary_request(content)
                and not _is_followup_diary_request(content)
                and not _is_any_button_action(content)
                and not _is_diary_reassert_request(content)
                and len(content) >= 5
            ):
                lines.append(f"{owner_label}: {content}")
    return "\n".join(lines).strip()


def _is_context_sufficient(context: str) -> bool:
    # 봇: 으로 시작하지 않는 라인에서 레이블 제거 후 user 텍스트 추출
    user_lines = []
    for line in context.splitlines():
        if line.startswith("봇: "):
            continue
        # "닉네임: 내용" 또는 "보호자: 내용" 형태에서 내용만 추출
        colon_idx = line.find(": ")
        if colon_idx != -1 and colon_idx < 20:
            user_lines.append(line[colon_idx + 2:])
        else:
            user_lines.append(line)
    user_text = " ".join(user_lines)
    if len(user_text) >= 20:
        return True
    has_event = any(kw in user_text for kw in _DIARY_EVENT_KEYWORDS)
    has_emotion = any(kw in user_text for kw in _DIARY_EMOTION_KEYWORDS)
    return has_event or has_emotion


def _detect_diary_sub_intent(query: str) -> str:
    q = (query or "").strip()

    # 1) 실제 일기 생성 의도가 있으면 guide보다 write 우선
    if (
        _is_explicit_diary_request(q)
        or _is_direct_diary_request(q)
        or _is_followup_diary_request(q)
        or _is_diary_create_request(q)
        or _is_diary_confirm_request(q)
        or _is_diary_reassert_request(q)
    ):
        return "write"

    # 2) 내용이 길면 설명 요청보다 일기 본문일 가능성이 훨씬 높음
    if len(q) >= 25:
        return "write"

    # 3) 안내성 분기
    if any(kw in q for kw in _GUIDE_CALENDAR_KEYWORDS):
        return "guide_calendar"

    if any(kw in q for kw in _GUIDE_ALBUM_KEYWORDS):
        return "guide_album"

    if any(kw in q for kw in _GUIDE_WRITE_KEYWORDS):
        return "guide_write"

    return "write"


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


# ── pet 컨텍스트 결정 결과 ────────────────────────────────────────────────────
# state 분기:
#   "ok"              → pet 결정 완료, 일기 생성 진행
#   "no_pets"         → 보유 활성 pet 0 마리, 등록 유도 응답 후 일기 생성 중단
#   "needs_selection" → primary_pet_id 와 ctx.pet_id 둘 다 없고 보유 pet 1+ 마리,
#                       선택 유도 응답 후 일기 생성 중단

PetContextState = Literal["ok", "no_pets", "needs_selection"]


@dataclass
class PetContextResult:
    """`_load_pet_context()` 결과 — 호출처가 state 로 분기."""

    state: PetContextState
    pet: dict
    available_pets: list[dict] = field(default_factory=list)


# 안내 문구 (placeholder — 톤 일관성은 PM 검토 후 정정)
_NO_PETS_MESSAGE = (
    "반려견을 먼저 등록해주세요. "
    "마이페이지에서 추가하신 후 다시 시도해주세요."
)


def _build_needs_selection_message(available_pets: list[dict]) -> str:
    """선택 유도 안내 메시지 — 보유 pet 목록(이름·견종) 포함."""
    if not available_pets:
        return "어떤 반려견의 일기를 쓸지 선택해주세요."

    bullets = "\n".join(
        f"- {p.get('name') or '이름 미등록'}"
        + (f" ({p['breed']})" if p.get("breed") else "")
        for p in available_pets
    )
    return (
        "어떤 반려견의 일기를 쓸지 선택해주세요.\n\n"
        f"보유한 반려견:\n{bullets}\n\n"
        "마이페이지에서 대표 반려견을 설정하거나, 화면에서 반려견을 먼저 선택해주세요."
    )


def _pet_summary(pet: Pet) -> dict:
    """선택 유도 응답에 노출할 pet 요약 (id/name/breed)."""
    breed_ko = getattr(pet.breed, "name_ko", None) if pet.breed else None
    return {
        "id": pet.id,
        "name": pet.name or "",
        "breed": breed_ko or "",
    }


def _build_pet_ctx(pet: Pet, owner_name: str) -> dict:
    """Pet ORM → LLM 프롬프트용 컨텍스트 dict (`_DEFAULT_DIARY_PET` 키 정합)."""
    breed_ko = getattr(pet.breed, "name_ko", None) if pet.breed else None
    breed_en = getattr(pet.breed, "name_en", None) if pet.breed else None
    birth_str: str | None = None
    if isinstance(pet.birth_date, date):
        birth_str = pet.birth_date.strftime("%Y-%m-%d")

    # AI 프로필 분석 결과에서 english_prompt / must_include_keywords 추출
    english_prompt = None
    must_include_keywords: list[str] = []
    if hasattr(pet, "profile") and pet.profile and pet.profile.profile_json:
        cs = pet.profile.profile_json.get("character_sheet", {})
        english_prompt = cs.get("english_prompt")
        must_include_keywords = cs.get("must_include_keywords", [])

    return {
        "pet_name": pet.name or _DEFAULT_DIARY_PET["pet_name"],
        "breed": breed_ko or _DEFAULT_DIARY_PET["breed"],
        "breed_en": breed_en,
        "birth_date": birth_str,
        "personalities": list(pet.selected_tags or []),
        "owner_name": owner_name,
        "pet_id": pet.id,
        "english_prompt": english_prompt,
        "must_include_keywords": must_include_keywords,
    }


async def _load_pet_context(ctx: Any) -> PetContextResult:
    """다이어리 응답용 pet 컨텍스트 결정 — 외부팀 QA ID 16 fix (2026-05-14).

    우선순위:
        1. `users.primary_pet_id` 가 활성 pet
        2. `ctx.pet_id` 가 본인 소유 활성 pet (사용자 명시 선택 override)
        3-A. 보유 활성 pet 0 마리 → state="no_pets"
        3-B. primary NULL + ctx.pet_id 없음 + 보유 pet 1+ 마리 → state="needs_selection"

    ctx 무효(`user_id`/`db` None) 케이스는 기존 동작 호환 — `state="ok"` + 기본 pet.
    """
    if getattr(ctx, "user_id", None) is None or getattr(ctx, "db", None) is None:
        return PetContextResult(state="ok", pet=dict(_DEFAULT_DIARY_PET))

    # 본인 소유 활성 pet 목록 조회 (created_at ASC = 가장 오래된 순)
    try:
        result = await ctx.db.execute(
            select(Pet)
            .where(Pet.user_id == ctx.user_id, Pet.deleted_at.is_(None))
            .options(selectinload(Pet.breed))
            .order_by(Pet.created_at.asc())
        )
        pets = list(result.scalars().all())
    except Exception as e:
        logger.warning(f"[Diary] 반려견 목록 조회 실패: {e}")
        return PetContextResult(state="ok", pet=dict(_DEFAULT_DIARY_PET))

    # 3-A: 보유 활성 pet 0 마리 → 등록 유도
    if not pets:
        return PetContextResult(state="no_pets", pet=dict(_DEFAULT_DIARY_PET))

    # owner_name + primary_pet_id 조회
    owner_name = ""
    primary_pet_id: int | None = None
    try:
        user_result = await ctx.db.execute(select(User).where(User.id == ctx.user_id))
        user = user_result.scalar_one_or_none()
        if user:
            owner_name = user.nickname or ""
            primary_pet_id = getattr(user, "primary_pet_id", None)
    except Exception as e:
        logger.warning(f"[Diary] 사용자 조회 실패: {e}")

    chosen_pet: Pet | None = None

    # 우선순위 2: ctx.pet_id override (본인 소유 활성 검증 — pets 안에 있어야 함)
    requested_pet_id = getattr(ctx, "pet_id", None)
    if requested_pet_id is not None:
        try:
            requested_pet_id_int = int(requested_pet_id)
            for pet in pets:
                if pet.id == requested_pet_id_int:
                    chosen_pet = pet
                    break
            if chosen_pet is None:
                logger.info(
                    f"[Diary] ctx.pet_id={requested_pet_id} 본인 소유 활성 pet 아님 "
                    f"→ primary 폴백 (silent)"
                )
        except (ValueError, TypeError):
            logger.info(f"[Diary] ctx.pet_id={requested_pet_id!r} 정수 변환 실패 → 무시")

    # 우선순위 1: primary_pet_id (override 못 잡았을 때만)
    if chosen_pet is None and primary_pet_id is not None:
        for pet in pets:
            if pet.id == primary_pet_id:
                chosen_pet = pet
                break
        if chosen_pet is None:
            logger.info(
                f"[Diary] users.primary_pet_id={primary_pet_id} 활성 pet 미일치 "
                f"(탈퇴/삭제 추정) → 선택 유도"
            )

    # 3-B: primary NULL + ctx.pet_id 없음 (또는 무효) + 보유 pet 1+ 마리 → 선택 유도
    if chosen_pet is None:
        return PetContextResult(
            state="needs_selection",
            pet=dict(_DEFAULT_DIARY_PET),
            available_pets=[_pet_summary(p) for p in pets],
        )

    # 우선순위 1 또는 2 → ok
    return PetContextResult(state="ok", pet=_build_pet_ctx(chosen_pet, owner_name))


async def _generate_diary_json(pet_ctx: dict, query: str) -> dict | None:
    if _contains_injection(query):
        logger.warning(f"[Diary] 인젝션 시도 차단: {query[:80]}")
        return None

    emotion = _infer_emotion(query)
    diary_type = _infer_diary_type(query)

    owner_label = pet_ctx.get("owner_name") or "보호자"

    if f"{owner_label}:" in query or "보호자:" in query or "봇:" in query:
        conversation_summary = query.strip()
        # 보호자 → 실제 닉네임 치환
        if owner_label != "보호자":
            conversation_summary = conversation_summary.replace("보호자:", f"{owner_label}:")
    else:
        conversation_summary = f"{owner_label}: {query.strip()}"

    prompt = _diary_prompt_builder.build_diary_prompt(
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
            messages=[
                {"role": "system", "content": _diary_prompt_builder.build_system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
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
    ctx: Any,
) -> tuple[str | None, int | None]:
    image_prompt = _diary_prompt_builder.build_final_image_prompt(
        image_prompt_base=diary_data.get("image_prompt_base", ""),
        breed=pet_ctx["breed"],
        breed_en=pet_ctx["breed_en"],
        birth_date=pet_ctx["birth_date"],
        personalities=pet_ctx["personalities"],
        all_answers=[diary_data.get("_conversation", "")],
        emotion=diary_data.get("_emotion", _DEFAULT_DIARY_EMOTION),
        english_prompt=pet_ctx.get("english_prompt"),
    )

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
            return None, None
    except Exception as e:
        logger.error(f"[Diary] 이미지 생성 호출 실패: {e}")
        return None, None

    try:
        image_bytes = base64.b64decode(b64)
        file_url = await _upload_to_s3(image_bytes, "diary.png", "image/png")
    except Exception as e:
        logger.error(f"[Diary] S3 업로드 실패: {e}")
        return None, None

    image_id: int | None = None
    if getattr(ctx, "db", None) is not None:
        try:
            image_row = Image(file_url=file_url, file_name="diary.png")
            ctx.db.add(image_row)
            await ctx.db.flush()
            image_id = image_row.id
        except Exception as e:
            logger.warning(f"[Diary] images 테이블 저장 실패 (URL 만 반환): {e}")

    return file_url, image_id


async def _save_diary_record(
    pet_ctx: dict,
    diary_data: dict,
    image_id: int | None,
    ctx: Any,
) -> bool:
    if getattr(ctx, "db", None) is None:
        logger.warning("[Diary] diary 저장 실패: db 세션 없음")
        return False
    if getattr(ctx, "user_id", None) is None:
        logger.warning("[Diary] diary 저장 실패: user_id 없음")
        return False
    if not pet_ctx.get("pet_id"):
        logger.warning("[Diary] diary 저장 실패: pet_id 없음")
        return False

    try:
        payload = DiaryCreate(
            pet_id=pet_ctx["pet_id"],
            image_id=image_id,
            when_text="",
            where_text="",
            who_text="보호자와 반려견",
            what_text=diary_data.get("_conversation", ""),
            how_text="자유채팅 그림일기 생성",
            why_text="",
            title=diary_data.get("title", "오늘의 일기"),
            content=diary_data.get("content", ""),
            summary=diary_data.get("summary", ""),
            emotion=diary_data.get("_emotion", _DEFAULT_DIARY_EMOTION),
        )
        await create_diary(payload, ctx.db, ctx.user_id)
        await ctx.db.commit()
        return True
    except Exception as e:
        logger.error(f"[Diary] diary 저장 실패: {e}")
        try:
            await ctx.db.rollback()
        except Exception:
            pass
        return False


async def _handle_diary(query: str, ctx: Any) -> str:
    pc_result = await _load_pet_context(ctx)
    if pc_result.state == "no_pets":
        return _NO_PETS_MESSAGE
    if pc_result.state == "needs_selection":
        return _build_needs_selection_message(pc_result.available_pets)

    pet_ctx = pc_result.pet
    diary_data = await _generate_diary_json(pet_ctx, query)

    if diary_data is None:
        return (
            "일기 생성에 실패했어요. 잠시 후 다시 시도하거나 "
            "/api/diary/generate 엔드포인트에서 직접 작성해주세요."
        )

    title = diary_data.get("title", "오늘의 일기")
    content = diary_data.get("content", "")
    summary = diary_data.get("summary", "")

    image_url, image_id = await _generate_and_store_image(pet_ctx, diary_data, ctx)
    if image_url and image_id:
        await _save_diary_record(pet_ctx, diary_data, image_id, ctx)

    lines = [f"📖 **{title}**", "", content]
    if summary:
        lines.extend(["", f"_요약_: {summary}"])
    if image_url:
        lines.extend(["", f"![{title}]({image_url})"])
    else:
        lines.extend([
            "",
            "📸 그림일기 이미지를 만들지 못했어요.",
            "**\"그림일기 만들어줘\"** 라고 입력하시면 이미지만 다시 시도해드릴게요!",
        ])

    return "\n".join(lines)


async def _generate_diary_text_only(query: str, ctx: Any) -> str:
    pc_result = await _load_pet_context(ctx)
    if pc_result.state == "no_pets":
        return _NO_PETS_MESSAGE
    if pc_result.state == "needs_selection":
        return _build_needs_selection_message(pc_result.available_pets)

    pet_ctx = pc_result.pet
    diary_data = await _generate_diary_json(pet_ctx, query)

    if diary_data is None:
        return "일기 생성에 실패했어요. 잠시 후 다시 시도해주세요."

    title = diary_data.get("title", "오늘의 일기")
    content = diary_data.get("content", "")
    summary = diary_data.get("summary", "")

    lines = [f"📖 **{title}**", "", content]
    if summary:
        lines.extend(["", f"_요약_: {summary}"])
    lines.extend(["", "마음에 드세요? 수정하거나 그림일기로 완성해드릴 수 있어요 😊"])
    lines.append(f"{_BUTTONS_MARKER}그림일기로 만들어줘|일기 다시 쓰고 싶어")

    return "\n".join(lines)


def _build_diary_proposal_response() -> str:
    return (
        "이야기 잘 들었어요 😊 이 내용으로 일기를 써볼까요?\n\n"
        f"{_BUTTONS_MARKER}일기 만들어줘|좀 더 이야기할래"
    )


async def _finalize_diary_and_save(query: str, ctx: Any) -> str:
    if getattr(ctx, "db", None) is None or getattr(ctx, "room_id", None) is None:
        return "그림일기를 완성하려면 대화방 정보가 필요해요. 다시 시도해주세요."

    from services.chat_message_service import list_messages

    recent = await list_messages(ctx.room_id, ctx.db, last_n=10)
    meaningful = _extract_meaningful_user_content(recent)
    effective = meaningful or query

    pc_result = await _load_pet_context(ctx)
    if pc_result.state == "no_pets":
        return _NO_PETS_MESSAGE
    if pc_result.state == "needs_selection":
        return _build_needs_selection_message(pc_result.available_pets)

    pet_ctx = pc_result.pet
    diary_data = await _generate_diary_json(pet_ctx, effective)
    if diary_data is None:
        return "그림일기 생성에 실패했어요. 잠시 후 다시 시도해주세요."

    image_url, image_id = await _generate_and_store_image(pet_ctx, diary_data, ctx)
    if not image_url:
        return "그림일기 이미지를 만들지 못했어요. 잠시 후 다시 시도해주세요."

    await _save_diary_record(pet_ctx, diary_data, image_id, ctx)

    title = diary_data.get("title", "오늘의 일기")
    content = diary_data.get("content", "")
    summary = diary_data.get("summary", "")

    lines = [f"📖 **{title}**", "", content]
    if summary:
        lines.extend(["", f"_요약_: {summary}"])
    lines.extend(["", f"![{title}]({image_url})"])
    return "\n".join(lines)


async def _ask_diary_followup(turn: int, ctx: Any) -> str:
    pc_result = await _load_pet_context(ctx)
    if pc_result.state == "no_pets":
        return _NO_PETS_MESSAGE
    if pc_result.state == "needs_selection":
        return _build_needs_selection_message(pc_result.available_pets)

    pet_ctx = pc_result.pet
    pet_name = pet_ctx.get("pet_name", "우리 아이")
    questions = [
        f"{pet_name}와 오늘 어떤 일이 있었나요? 조금 더 이야기해주세요 😊",
        f"{pet_name}의 표정이나 행동 중 특별히 기억에 남는 순간이 있었나요?",
        f"오늘 가장 행복했거나 인상 깊었던 순간은 어떤 감정이었나요?",
    ]
    return questions[min(turn, len(questions) - 1)]


async def _handle_diary_mini_flow(query: str, ctx: Any) -> str:
    # ── 인젝션/탈옥 사전 차단 (LLM 호출 전) ──────────────────────────────
    if _contains_injection(query):
        logger.warning(f"[DiaryMiniFlow] 인젝션 시도 차단: {query[:80]}")
        return _INJECTION_RESPONSE

    is_explicit = _is_explicit_diary_request(query)
    is_direct = _is_direct_diary_request(query)
    is_followup = _is_followup_diary_request(query)
    is_reassert = _is_diary_reassert_request(query)

    # 순수 시작 요청("일기 써줘", "그림일기 쓸래" 등) → 맥락 없으면 프론트엔드 플로우 트리거
    if _is_diary_start_flow_request(query):
        has_context = False
        if getattr(ctx, "db", None) is not None and getattr(ctx, "room_id", None) is not None:
            try:
                from services.chat_message_service import list_messages
                recent = await list_messages(ctx.room_id, ctx.db, last_n=10)
                meaningful = _extract_meaningful_user_content(recent)
                has_context = bool(meaningful and _is_context_sufficient(f"보호자: {meaningful}"))
            except Exception:
                pass
        if not has_context:
            logger.info("[DiaryMiniFlow] 순수 시작 요청 → 프론트엔드 다이어리 플로우 트리거")
            return _DIARY_FLOW_TRIGGER

    if getattr(ctx, "db", None) is not None and getattr(ctx, "room_id", None) is not None:
        try:
            from services.chat_message_service import list_messages

            recent = await list_messages(ctx.room_id, ctx.db, last_n=10)
            context = _collect_diary_context(recent)
            bots = [m for m in recent if m.role == "assistant"]
            last_bot_raw = (bots[-1].content if bots else "") or ""
            last_bot = _strip_buttons(last_bot_raw)

            if _is_image_generation_request(query):
                logger.info("[DiaryMiniFlow] 그림일기 생성 버튼 → 저장 후 완료 메시지")
                return await _finalize_diary_and_save(query, ctx)

            if _is_diary_create_request(query):
                logger.info("[DiaryMiniFlow] '일기 만들어줘' 버튼 → 텍스트 일기 생성")
                meaningful = _extract_meaningful_user_content(recent)
                effective = meaningful or context or query
                return await _generate_diary_text_only(effective, ctx)

            # 긴 입력 + 명시적 일기 요청이면 추가 질문 대신 버튼 제안
            if len(query.strip()) >= 40 and _is_explicit_diary_request(query):
                logger.info("[DiaryMiniFlow] 긴 입력 + 명시적 요청 → 버튼 제안")
                return _build_diary_proposal_response()

            if _is_diary_revision_request(query):
                return "어떤 부분을 수정할까요? 원하시는 내용을 알려주세요 ✏️"

            if _is_continue_chat_request(query):
                user_cnt = sum(
                    1 for m in recent
                    if m.role == "user"
                    and m.content
                    and not _is_any_button_action(m.content)
                    and not _is_explicit_diary_request(m.content)
                )
                return await _ask_diary_followup(user_cnt, ctx)

            if _is_diary_confirm_request(query):
                if _is_diary_draft_message(last_bot_raw):
                    draft = _extract_draft_text(last_bot_raw)
                    logger.info("[DiaryMiniFlow] 일기 초안 확정 → 최종 출력")
                    return (
                        f"좋아요! 일기를 완성했어요 ✨\n\n{draft}\n\n"
                        f"{_BUTTONS_MARKER}그림일기로 만들어줘|일기 다시 쓰고 싶어"
                    )
                logger.info("[DiaryMiniFlow] confirm이지만 직전 봇이 초안 아님 → 일기 문맥 재유도")
                return "방금 이야기한 내용을 바탕으로 일기를 다시 정리해드릴까요? 😊"

            if is_reassert:
                meaningful = _extract_meaningful_user_content(recent)
                effective = meaningful or context or query
                logger.info("[DiaryMiniFlow] 재강조 일기 요청 → 텍스트 일기 생성")
                return await _generate_diary_text_only(effective, ctx)

            if is_followup:
                meaningful = _extract_meaningful_user_content(recent)
                if meaningful and _is_context_sufficient(f"보호자: {meaningful}"):
                    logger.info("[DiaryMiniFlow] follow-up 요청 + 충분한 맥락 → 버튼 제안")
                    return _build_diary_proposal_response()
                if meaningful:
                    logger.info("[DiaryMiniFlow] follow-up 요청 + 부분 맥락 → 버튼 제안")
                    return _build_diary_proposal_response()
                return await _ask_diary_followup(0, ctx)

            if is_direct:
                meaningful = _extract_meaningful_user_content(recent)
                effective = meaningful or context or query
                logger.info("[DiaryMiniFlow] 즉시 요청 → 텍스트 일기 생성")
                return await _generate_diary_text_only(effective, ctx)

            if is_explicit:
                meaningful = _extract_meaningful_user_content(recent)
                effective = meaningful or context or query
                if _is_context_sufficient(f"보호자: {effective}") or len(effective.strip()) >= 20:
                    logger.info("[DiaryMiniFlow] 명시적 요청 + 충분한 맥락 → 버튼 제안")
                    return _build_diary_proposal_response()
                return await _ask_diary_followup(0, ctx)

            if "어떤 부분을 수정할까요" in last_bot:
                logger.info("[DiaryMiniFlow] 수정 응답 → 기존 초안 기반 재생성")
                prev_draft_raw = (bots[-2].content if len(bots) >= 2 else "") or ""
                prev_draft = _extract_draft_text(prev_draft_raw) if prev_draft_raw else ""
                revision_ctx = (
                    f"기존 일기 초안:\n{prev_draft}\n\n"
                    f"{context}\n"
                    f"수정 요청: {query}"
                ).strip()
                return await _generate_diary_text_only(revision_ctx or query, ctx)

            user_content_msgs = [
                m for m in recent
                if m.role == "user"
                and m.content
                and not _is_explicit_diary_request(m.content)
                and not _is_direct_diary_request(m.content)
                and not _is_any_button_action(m.content)
            ]

            if last_bot and any(marker in last_bot for marker in _FOLLOW_UP_MARKERS):
                turn = len(user_content_msgs)
                if turn >= 3 and _is_context_sufficient(context):
                    logger.info("[DiaryMiniFlow] 3턴 이상 Q&A 완료 → 버튼 제안")
                    return _build_diary_proposal_response()
                return await _ask_diary_followup(turn, ctx)

        except Exception as e:
            logger.warning(f"[DiaryMiniFlow] 히스토리 조회 실패: {e}")

    # 히스토리 없는 경우
    if is_direct:
        return await _generate_diary_text_only(query, ctx)

    if is_explicit or is_reassert:
        if len(query.strip()) >= 20:
            return _build_diary_proposal_response()
        return await _ask_diary_followup(0, ctx)

    if len(query.strip()) >= 40 and (
        any(kw in query for kw in _DIARY_EVENT_KEYWORDS)
        or any(kw in query for kw in _DIARY_EMOTION_KEYWORDS)
    ):
        return _build_diary_proposal_response()

    if is_followup:
        return await _ask_diary_followup(0, ctx)

    return await _ask_diary_followup(0, ctx)