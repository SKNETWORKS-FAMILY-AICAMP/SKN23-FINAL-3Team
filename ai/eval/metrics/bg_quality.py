"""
ai/eval/metrics/bg_quality.py
배경 품질 (Background Quality) — 가중치 35%

PIL 기반 지표:
  - 밝기 적정 여부 (너무 어둡거나 밝으면 감점)
  - 선명도 추정 (엣지 분산 — 낮으면 배경 뭉개짐)
  - 색 다양성 (너무 단조롭거나 너무 극단적이면 감점)

YOLO가 있으면 배경 영역(강아지 bbox 제외)만 크롭해서 평가.
없으면 전체 이미지 기준으로 계산.
"""

from __future__ import annotations
import base64
import io
import math

try:
    from PIL import Image, ImageFilter
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


def _decode_image(b64_str: str):
    if not _PIL_AVAILABLE:
        return None
    try:
        raw = base64.b64decode(b64_str)
        return Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception:
        return None


def _brightness(img: "Image.Image") -> float:
    img_small = img.resize((128, 128))
    pixels = list(img_small.getdata())
    total = sum(0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels)
    return total / len(pixels)


def _sharpness(img: "Image.Image") -> float:
    """엣지 분산 — 높을수록 선명"""
    gray = img.convert("L").resize((256, 256))
    edges = gray.filter(ImageFilter.FIND_EDGES)
    pixels = list(edges.getdata())
    mean = sum(pixels) / len(pixels)
    return sum((p - mean) ** 2 for p in pixels) / len(pixels)


def _color_diversity(img: "Image.Image") -> float:
    """RGB 채널 표준편차 평균"""
    img_small = img.resize((128, 128))
    r_vals, g_vals, b_vals = [], [], []
    for r, g, b in img_small.getdata():
        r_vals.append(r); g_vals.append(g); b_vals.append(b)

    def std(vals):
        n = len(vals)
        m = sum(vals) / n
        return math.sqrt(sum((v - m) ** 2 for v in vals) / n)

    return (std(r_vals) + std(g_vals) + std(b_vals)) / 3.0


def score_bg_quality(image_b64: str) -> dict:
    """
    Returns:
        {
          "bg_quality": 0~100 | None,
          "brightness": float | None,
          "sharpness_estimate": float | None,
          "color_diversity": float | None,
        }
    """
    empty = {
        "bg_quality": None,
        "brightness": None,
        "sharpness_estimate": None,
        "color_diversity": None,
    }

    if not _PIL_AVAILABLE:
        return empty

    img = _decode_image(image_b64)
    if img is None:
        return empty

    brightness = _brightness(img)
    sharpness = _sharpness(img)
    diversity = _color_diversity(img)

    # 밝기 점수: 80~200이 적정 (그림책 밝은 느낌)
    brightness_score = 100 - abs(brightness - 150) * 0.55
    brightness_score = max(0.0, min(100.0, brightness_score))

    # 선명도 점수: 분산 500 이상이면 만점 (배경이 선명하게 그려짐)
    sharpness_score = min(100.0, sharpness / 5.0)

    # 색 다양성 점수: 20~65가 그림책 파스텔 범위
    diversity_score = 100 - abs(diversity - 42) * 1.3
    diversity_score = max(0.0, min(100.0, diversity_score))

    # 가중 합산
    score = brightness_score * 0.30 + sharpness_score * 0.45 + diversity_score * 0.25

    return {
        "bg_quality": round(score, 1),
        "brightness": round(brightness, 1),
        "sharpness_estimate": round(sharpness, 1),
        "color_diversity": round(diversity, 1),
    }
