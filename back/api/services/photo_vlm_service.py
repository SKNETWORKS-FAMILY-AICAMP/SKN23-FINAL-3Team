# -*- coding: utf-8 -*-
"""
services/photo_vlm_service.py
------------------------------
Qwen2.5-VL 기반 이미지 설명 추출 서비스.

역할:
  - 실사 사진 여부 판별 (is_real_photo)
  - 강아지별 외형 묘사 추출 (dog_visual_descriptions)
  - 장면 묘사 추출 (scene_description)
  - 보호자 외형 묘사 추출 (person_visual_description)

동작 모드:
  PHOTO_STYLE_MOCK_MODE=true  → mock 데이터 즉시 반환 (기본값, 개발용)
  USE_LOCAL_VLM=false         → None 반환, YOLO 결과만으로 검증
  USE_LOCAL_VLM=true          → 로컬 Qwen2.5-VL 모델 사용 (대용량 다운로드 필요)
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# transformers / qwen_vl_utils 없으면 VLM 비활성
try:
    from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
    from qwen_vl_utils import process_vision_info
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    _TRANSFORMERS_AVAILABLE = False
    logger.warning("[PhotoVLM] transformers/qwen_vl_utils 미설치 — VLM 비활성")


@dataclass
class VLMResult:
    is_real_photo: bool
    dog_visual_descriptions: list = field(default_factory=list)
    scene_description: str = ""
    person_visual_description: str = ""


# ── Mock ─────────────────────────────────────────────────────────────────────

_MOCK_VLM_RESULT = VLMResult(
    is_real_photo=True,
    dog_visual_descriptions=["small fluffy white dog with long silky coat and round dark eyes"],
    scene_description="a dog and person enjoying time together outdoors",
    person_visual_description="person in casual clothes with the dog",
)

# ── Singleton 모델 ────────────────────────────────────────────────────────────

_vlm_model = None
_vlm_processor = None


def _get_vlm_model_and_processor(model_name: str):
    global _vlm_model, _vlm_processor
    if _vlm_model is None:
        import torch
        logger.info(f"[PhotoVLM] 모델 로드 중: {model_name}")
        _vlm_model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype="auto",
            device_map="auto",
        )
        _vlm_processor = AutoProcessor.from_pretrained(model_name)
        logger.info("[PhotoVLM] 모델 로드 완료")
    return _vlm_model, _vlm_processor


# ── 동기 추론 ─────────────────────────────────────────────────────────────────

_ANALYSIS_PROMPT = """\
Analyze this image and return a JSON object with these exact fields:
- is_real_photo (bool): true if this is a real photograph taken with a camera; \
false if it is AI-generated art, illustration, cartoon, screenshot, or CGI
- dog_visual_descriptions (list of str): for each dog visible, one concise English description \
(max 20 words) of its fur color, coat length/texture, body size, ear shape, and any markings — \
describe exactly what you see, do NOT guess breed name
- scene_description (str): brief English scene description including setting and what subjects are doing (max 25 words)
- person_visual_description (str): brief English description of the person if visible, \
e.g. clothing color and rough appearance (max 15 words); empty string if no person

Return ONLY valid JSON. No markdown, no explanation."""


def _analyze_sync(image_bytes: bytes, mime_type: str, model_name: str) -> VLMResult:
    model, processor = _get_vlm_model_and_processor(model_name)

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": data_url},
                {"type": "text", "text": _ANALYSIS_PROMPT},
            ],
        }
    ]

    text = processor.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    image_inputs, video_inputs = process_vision_info(messages)
    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(model.device)

    generated_ids = model.generate(**inputs, max_new_tokens=512)
    trimmed = [
        out[len(inp):]
        for inp, out in zip(inputs.input_ids, generated_ids)
    ]
    raw = processor.batch_decode(
        trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False
    )[0]

    return _parse_vlm_output(raw)


def _parse_vlm_output(raw: str) -> VLMResult:
    raw = raw.strip()
    # JSON 블록 추출 (마크다운 펜스 무시)
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        data = json.loads(m.group()) if m else {}

    descriptions = data.get("dog_visual_descriptions", [])
    if not isinstance(descriptions, list):
        descriptions = []

    return VLMResult(
        is_real_photo=bool(data.get("is_real_photo", True)),
        dog_visual_descriptions=[str(d) for d in descriptions],
        scene_description=str(data.get("scene_description", "")),
        person_visual_description=str(data.get("person_visual_description", "")),
    )


# ── 공개 API ──────────────────────────────────────────────────────────────────

async def analyze(image_bytes: bytes, mime_type: str) -> Optional[VLMResult]:
    """
    이미지를 VLM으로 분석합니다.

    Returns:
        VLMResult  — 분석 성공
        None       — USE_LOCAL_VLM=false (VLM 비활성)
    Raises:
        Exception  — 모델 추론 실패 (호출부에서 catch)
    """
    from core.config import settings

    if settings.PHOTO_STYLE_MOCK_MODE:
        logger.debug("[PhotoVLM] mock 모드 — 고정 결과 반환")
        return _MOCK_VLM_RESULT

    if not settings.USE_LOCAL_VLM:
        logger.debug("[PhotoVLM] USE_LOCAL_VLM=false — VLM 건너뜀")
        return None

    if not _TRANSFORMERS_AVAILABLE:
        logger.warning("[PhotoVLM] transformers 없음 — VLM 건너뜀")
        return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None, _analyze_sync, image_bytes, mime_type, settings.VLM_MODEL_NAME
    )
