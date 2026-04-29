"""
ai/eval/metrics/style_consistency.py
스타일 일관성 (Style Consistency) — 가중치 25%

sentence-transformers의 CLIP 모델로 이미지 임베딩 계산 후
레퍼런스 이미지 셋 평균 임베딩과 코사인 유사도를 측정.

레퍼런스 셋이 없으면:
  - 프롬프트 텍스트 임베딩 vs. 이미지 임베딩 코사인 유사도로 대체
  - (CLIP은 텍스트-이미지 동일 공간 임베딩 지원)

레퍼런스 이미지 추가 방법:
  ai/eval_data/reference_images/ 폴더에 PNG/JPG 파일을 넣으면
  다음 실행 시 자동으로 참조셋 갱신.
"""

from __future__ import annotations
import base64
import io
import json
import math
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    from PIL import Image
    _ST_AVAILABLE = True
except ImportError:
    _ST_AVAILABLE = False

_REFERENCE_DIR = Path(__file__).parent.parent.parent / "eval_data" / "reference_images"
_CACHE_FILE = Path(__file__).parent.parent.parent / "eval_data" / "reference_embedding_cache.json"

_model = None
_reference_embedding: list[float] | None = None


def _get_model():
    global _model
    if _model is None:
        # CLIP ViT-B/32 — sentence-transformers에 포함
        _model = SentenceTransformer("clip-ViT-B-32")
    return _model


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x ** 2 for x in a))
    norm_b = math.sqrt(sum(x ** 2 for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _load_reference_embedding() -> list[float] | None:
    """레퍼런스 이미지 폴더에서 평균 임베딩 로드 (캐시 우선)"""
    global _reference_embedding
    if _reference_embedding is not None:
        return _reference_embedding

    if not _REFERENCE_DIR.exists():
        return None

    ref_images = list(_REFERENCE_DIR.glob("*.png")) + list(_REFERENCE_DIR.glob("*.jpg"))
    if not ref_images:
        return None

    # 캐시 확인 (이미지 파일 수 같으면 재사용)
    if _CACHE_FILE.exists():
        try:
            cache = json.loads(_CACHE_FILE.read_text(encoding="utf-8"))
            if cache.get("count") == len(ref_images):
                _reference_embedding = cache["embedding"]
                return _reference_embedding
        except Exception:
            pass

    try:
        model = _get_model()
        imgs = [Image.open(p).convert("RGB") for p in ref_images]
        embeddings = model.encode(imgs, convert_to_numpy=True)
        avg = (embeddings.sum(axis=0) / len(embeddings)).tolist()
        _CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_FILE.write_text(
            json.dumps({"count": len(ref_images), "embedding": avg}),
            encoding="utf-8",
        )
        _reference_embedding = avg
        return avg
    except Exception:
        return None


def _embed_image(image_b64: str) -> list[float] | None:
    try:
        raw = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        model = _get_model()
        emb = model.encode([img], convert_to_numpy=True)[0]
        return emb.tolist()
    except Exception:
        return None


def _embed_text(text: str) -> list[float] | None:
    try:
        model = _get_model()
        emb = model.encode([text], convert_to_numpy=True)[0]
        return emb.tolist()
    except Exception:
        return None


def score_style_consistency(image_b64: str, image_prompt: str = "") -> dict:
    """
    레퍼런스 셋이 있으면 레퍼런스 기반, 없으면 텍스트-이미지 정합도로 대체.

    Returns:
        {
          "style_consistency": 0~100 | None,
          "style_similarity_raw": float | None,  # 코사인 유사도 -1~1
          "reference_mode": "reference_set" | "text_image" | "unavailable",
        }
    """
    empty = {
        "style_consistency": None,
        "style_similarity_raw": None,
        "reference_mode": "unavailable",
    }

    if not _ST_AVAILABLE:
        return empty

    img_emb = _embed_image(image_b64)
    if img_emb is None:
        return empty

    ref_emb = _load_reference_embedding()

    if ref_emb is not None:
        # 레퍼런스 셋 기반
        sim = _cosine_similarity(img_emb, ref_emb)
        mode = "reference_set"
    elif image_prompt:
        # 텍스트-이미지 정합도로 대체
        txt_emb = _embed_text(image_prompt[:500])
        if txt_emb is None:
            return empty
        sim = _cosine_similarity(img_emb, txt_emb)
        mode = "text_image"
    else:
        return empty

    # 코사인 유사도 (-1~1) → 0~100 점수
    score = (sim + 1) / 2 * 100
    score = max(0.0, min(100.0, score))

    return {
        "style_consistency": round(score, 1),
        "style_similarity_raw": round(sim, 4),
        "reference_mode": mode,
    }
