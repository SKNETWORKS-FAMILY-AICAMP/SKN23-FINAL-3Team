# -*- coding: utf-8 -*-
"""
services/intent_service.py
--------------------------
KoELECTRA 기반 의도 분류 서비스.

학습 모델 경로: <project_root>/ai/intent/model/
(환경변수 INTENT_MODEL_DIR 로 재정의 가능)

분류 레이블:
    - "다이어리 작성"  → 강아지 시점 일기 생성
    - "장소추천"       → 반려견 동반 가능 장소 추천
    - "시설정보"       → 특정 시설 상세 정보

[모델 로딩]
최초 호출 시 lazy-load 하며, 프로세스 내 싱글톤으로 유지됩니다.
warmup_intent_model() 을 앱 lifespan 에서 호출하면 첫 요청 지연을 없앨 수 있습니다.

[스레드 안전성]
transformers 추론은 스레드 안전하지 않을 수 있어, asyncio 환경에서는
run_in_executor 로 감싸서 호출합니다 (classify_intent_async).
"""

from __future__ import annotations

import os
import json
import torch
import asyncio
import logging
import threading

from typing import Any
from dataclasses import dataclass
from transformers import ElectraForSequenceClassification, ElectraTokenizer

logger = logging.getLogger(__name__)


# ── 경로 설정 ────────────────────────────────────────────────────────────────
# back/api/services/intent_service.py → <project_root>/ai/intent/model
_DEFAULT_MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "ai", "intent", "model")
)
MODEL_DIR = os.getenv("INTENT_MODEL_DIR", _DEFAULT_MODEL_DIR)


# ── RAG 전략 맵 (각 의도별 다운스트림 서비스 힌트) ────────────────────────────
RAG_STRATEGY_MAP: dict[str, dict[str, Any]] = {
    "다이어리 작성": {
        "collection": "diary",
        "top_k": 3,
        "description": "강아지 행동 과학 지식 검색 → 감정 추론 → 강아지 시점 일기 생성",
    },
    "장소추천": {
        "collection": "places",
        "top_k": 5,
        "description": "반려견 동반 가능 장소 데이터베이스 검색",
    },
    "시설정보": {
        "collection": "places",
        "top_k": 1,
        "description": "특정 시설 상세 정보 검색",
    },
}


@dataclass(frozen=True)
class IntentResult:
    """의도 분류 결과."""
    intent: str                 # 분류된 의도 레이블
    confidence: float           # 0.0 ~ 1.0
    strategy: dict[str, Any]    # RAG_STRATEGY_MAP 항목


# ── 내부 싱글톤 상태 ──────────────────────────────────────────────────────────
_tokenizer: ElectraTokenizer | None = None
_model: ElectraForSequenceClassification | None = None
_id2label: dict[str, str] | None = None
_load_lock = threading.Lock()


def _load_model() -> None:
    """모델·토크나이저·레이블맵을 로드합니다 (동기, 한 번만 실행)."""
    global _tokenizer, _model, _id2label

    if _model is not None:
        return

    with _load_lock:
        if _model is not None:  # 더블 체크
            return

        if not os.path.isdir(MODEL_DIR):
            raise FileNotFoundError(
                f"의도 분류 모델 폴더가 없습니다: {MODEL_DIR}\n"
                f"환경변수 INTENT_MODEL_DIR 로 경로를 지정하거나 "
                f"ai/intent/model/ 에 학습된 모델을 두세요."
            )

        logger.info(f"[Intent] 모델 로딩 시작: {MODEL_DIR}")
        _tokenizer = ElectraTokenizer.from_pretrained(MODEL_DIR)
        model = ElectraForSequenceClassification.from_pretrained(MODEL_DIR)
        model.eval()
        _model = model

        with open(os.path.join(MODEL_DIR, "label_map.json"), "r", encoding="utf-8") as f:
            _id2label = json.load(f)["id2label"]

        logger.info("[Intent] 의도 분류 모델 로딩 완료")


def classify_intent(text: str) -> IntentResult:
    """
        입력 텍스트의 의도를 분류합니다 (동기).

        Args:
                text: 사용자 입력 텍스트 (공백 제거 후 비어있으면 ValueError)

        Returns:
                IntentResult(intent, confidence, strategy)

        Raises:
                ValueError        : 빈 텍스트
                FileNotFoundError : 모델 폴더 미존재
    """
    if not text or not text.strip():
        raise ValueError("분류할 텍스트가 비어 있습니다.")

    _load_model()
    assert _tokenizer is not None and _model is not None and _id2label is not None

    encoding = _tokenizer(
        text,
        max_length=128,
        padding="max_length",
        truncation=True,
        return_tensors="pt",
    )

    with torch.no_grad():
        logits = _model(**encoding).logits
        probs = torch.softmax(logits, dim=-1)[0]
        pred_id = int(torch.argmax(probs).item())

    intent = _id2label[str(pred_id)]
    confidence = round(float(probs[pred_id].item()), 4)
    strategy = RAG_STRATEGY_MAP.get(intent, RAG_STRATEGY_MAP["장소추천"])

    return IntentResult(intent=intent, confidence=confidence, strategy=strategy)


async def classify_intent_async(text: str) -> IntentResult:
    """
        비동기 래퍼. FastAPI 이벤트 루프를 블로킹하지 않도록
        classify_intent() 를 스레드 풀에서 실행합니다.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, classify_intent, text)


def warmup_intent_model() -> None:
    """
        앱 시작 시점에 호출하여 모델을 미리 로드합니다.
        실패해도 예외를 삼키고 경고만 남깁니다 (lifespan 차단 방지).
    """
    try:
        _load_model()
    except Exception as e:
        logger.warning(f"[Intent] 모델 워밍업 실패 (최초 요청 시 재시도): {e}")
