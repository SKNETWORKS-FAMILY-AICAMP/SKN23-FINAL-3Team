# -*- coding: utf-8 -*-
"""
utils/profanity_filter.py
-------------------------
한국어 욕설·비속어 차단 필터.

라이브러리: HuggingFace `smilegate-ai/kor_unsmile` (KoELECTRA 파인튜닝, 9개 혐오/욕설 라벨).
사유: korcen-ml PyPI 미등록·의존성 명세 부족 → 안정성·CI 신뢰성 위해 백업(c) 채택.
KoELECTRA 인프라(intent_service)와 동일 스택 → 추가 PyPI 의존성 0건.

[적용 5곳] (service 레이어에서 호출)
    - users.nickname           (user_service.update_user)
    - pets.name                (pet_service.create_pet, update_pet)
    - chat_rooms.title         (chat_room_service.create / update_title)
    - diaries.title·content·6W (diary_service.create_diary, update_diary)

[미적용]
    - 챗봇 채팅 메시지 (의도분류·GPT API 가 흡수)

[모델 로딩]
최초 호출 시 lazy-load 하며, 프로세스 내 싱글톤으로 유지됩니다.
warmup_profanity_model() 을 앱 lifespan 에서 호출하면 첫 요청 지연을 없앨 수 있습니다.
실패 시 lazy-load 폴백 + 통과 처리 (보수적 fail-open — 검열 누락 < 정상 입력 차단).

[테스트 고립성]
contains_profanity() 는 단일 함수로 노출 — pytest monkeypatch 가능.
"""

from __future__ import annotations

import logging
import threading

logger = logging.getLogger(__name__)

# smilegate-ai/kor_unsmile 의 9개 분류 라벨. 'clean' 만 비-혐오 — 나머지는 차단 대상.
_PROFANITY_LABELS: set[str] = {
    "여성/가족", "남성", "성소수자", "인종/국적", "연령",
    "지역", "종교", "기타 혐오", "악플/욕설",
}
_MODEL_NAME = "smilegate-ai/kor_unsmile"
_THRESHOLD = 0.75

# 일상 비속어 사전 — kor_unsmile 모델이 혐오·차별 라벨 위주라 일상 비속어
# (예: "바보") 를 false negative 로 놓치는 한계 보완. 부분 문자열 매칭이라
# false positive 가능성 ("바보스럽다") 있으나 차단 우선 정책 (#71, 사용자 결정 2026-05-07).
_LOCAL_PROFANITY_WORDS: set[str] = {
    # 일상 비속어 (한글)
    "바보", "멍청이", "쪼다", "또라이", "찌질이",
    "병신", "ㅂㅅ", "ㅄ",
    "씨발", "씨바", "ㅅㅂ", "ㅆㅂ",
    "개새끼", "개새", "씹새끼", "씹새",
    "지랄", "ㅈㄹ",
    "꺼져", "닥쳐", "엿먹어",
    # 영문
    "fuck", "shit", "bitch",
}

_pipeline = None
_load_lock = threading.Lock()


def _load_pipeline():
    """모델·토크나이저를 로드합니다 (동기, 한 번만 실행). 더블 체크 잠금."""
    global _pipeline
    if _pipeline is not None:
        return _pipeline
    with _load_lock:
        if _pipeline is not None:
            return _pipeline
        from transformers import pipeline as hf_pipeline
        _pipeline = hf_pipeline(
            "text-classification",
            model=_MODEL_NAME,
            top_k=None,  # 모든 라벨 score 반환 (return_all_scores deprecated 대체)
        )
        logger.info("[Profanity] 모델 로드 완료: %s", _MODEL_NAME)
    return _pipeline


def contains_profanity(text: str | None) -> bool:
    """문자열에 욕설·혐오 표현이 포함됐는지 판정.

    1차: 일상 비속어 사전 (`_LOCAL_PROFANITY_WORDS`, 부분 문자열 매칭).
    2차: ML 분류 (`smilegate-ai/kor_unsmile`, 9개 혐오 라벨, _THRESHOLD 초과).
    사전 OR ML 어느 쪽이라도 양성이면 True.

    Args:
        text: 검사 대상 (None / 빈 문자열은 False 반환).

    Returns:
        True  = 사전 매칭 OR ML 라벨 score 가 _THRESHOLD(0.5) 초과 시.
        False = clean, 입력 부재, 또는 ML 호출 실패 시 (fail-open — 사전 매칭은 항상 동작).
    """
    if not text or not text.strip():
        return False
    # 1차: 일상 비속어 사전 (부분 문자열). lower() 로 영문 대소문자 무시
    cleaned = text.strip().lower()
    for word in _LOCAL_PROFANITY_WORDS:
        if word in cleaned:
            return True
    # 2차: ML 분류 (혐오·차별 라벨)
    try:
        pipe = _load_pipeline()
        result = pipe(text)
        # transformers pipeline 응답: top_k=None 시 [[{"label": "...", "score": float}, ...]]
        scores = result[0] if result and isinstance(result[0], list) else result
        for entry in scores:
            label = entry.get("label", "")
            score = float(entry.get("score", 0.0))
            if label in _PROFANITY_LABELS and score >= _THRESHOLD:
                return True
    except Exception as e:
        logger.warning("[Profanity] 검사 실패 (통과 처리): %s", e)
        return False
    return False


def warmup_profanity_model() -> None:
    """앱 시작 시점에 호출해 모델을 미리 로드합니다.

    실패해도 예외를 삼키고 경고만 남깁니다 (lifespan 차단 방지).
    """
    try:
        _load_pipeline()
    except Exception as e:
        logger.warning("[Profanity] 모델 워밍업 실패 (최초 요청 시 재시도): %s", e)
