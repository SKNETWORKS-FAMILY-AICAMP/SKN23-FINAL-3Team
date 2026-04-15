"""
ai/eval/metrics/subject_purity.py
피사체 순도 (Subject Purity) — 가중치 40%

그림일기는 일러스트 스타일이므로 YOLO(실사 기반) 대신
CLIP 텍스트-이미지 유사도로 강아지/사람 존재 여부를 판단.

  - "a dog" 유사도 → 강아지 존재 확률
  - "a person" 유사도 → 사람 존재 확률
  - 강아지 확률 높고 사람 확률 낮을수록 높은 점수
"""

from __future__ import annotations
import base64
import io
import math

try:
    from sentence_transformers import SentenceTransformer
    from PIL import Image
    _CLIP_AVAILABLE = True
except ImportError:
    _CLIP_AVAILABLE = False

_model = None

# CLIP 판단 기준 텍스트
_DOG_PROMPTS   = ["a dog", "a cute dog", "a puppy", "a cartoon dog"]
_HUMAN_PROMPTS = ["a person", "a human", "a child", "a man", "a woman"]
_CLEAN_PROMPTS = ["a dog only", "only a dog with no people"]


def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("clip-ViT-B-32")
    return _model


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x**2 for x in a))
    nb = math.sqrt(sum(x**2 for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def _decode_image(b64_str: str):
    try:
        raw = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None


def score_subject_purity(image_b64: str) -> dict:
    """
    Returns:
        {
          "subject_purity": 0~100 | None,
          "dog_detected": bool | None,
          "human_detected": bool | None,
          "dog_area_ratio": None,      # CLIP 방식에선 미사용
          "extra_area_ratio": None,    # CLIP 방식에선 미사용
          "detected_labels": list[str],
        }
    """
    empty = {
        "subject_purity": None,
        "dog_detected": None,
        "human_detected": None,
        "dog_area_ratio": None,
        "extra_area_ratio": None,
        "detected_labels": [],
    }

    if not _CLIP_AVAILABLE:
        return empty

    img = _decode_image(image_b64)
    if img is None:
        return empty

    img.thumbnail((224, 224))

    try:
        model = _get_model()
        img_emb = model.encode([img], convert_to_numpy=True)[0].tolist()

        # 텍스트 프롬프트 임베딩
        dog_embs   = model.encode(_DOG_PROMPTS,   convert_to_numpy=True)
        human_embs = model.encode(_HUMAN_PROMPTS, convert_to_numpy=True)

        dog_score   = max(_cosine_sim(img_emb, e.tolist()) for e in dog_embs)
        human_score = max(_cosine_sim(img_emb, e.tolist()) for e in human_embs)

    except Exception:
        return empty

    # 임계값 기준으로 감지 여부 판단
    dog_detected   = dog_score   > 0.22
    human_detected = human_score > 0.22

    # 점수 계산
    # 강아지 있고 사람 없으면 높은 점수
    # 강아지 점수를 0~1 → 0~100 정규화 (CLIP 유사도 범위 고려)
    dog_norm   = max(0.0, (dog_score - 0.15) / 0.20)    # 0.15~0.35 → 0~1
    human_norm = max(0.0, (human_score - 0.15) / 0.20)  # 높을수록 감점

    score = dog_norm * 100 - human_norm * 60
    score = max(0.0, min(100.0, score))

    labels = []
    if dog_detected:
        labels.append("dog")
    if human_detected:
        labels.append("person")

    return {
        "subject_purity": round(score, 1),
        "dog_detected": dog_detected,
        "human_detected": human_detected,
        "dog_area_ratio": None,
        "extra_area_ratio": None,
        "detected_labels": labels,
    }
