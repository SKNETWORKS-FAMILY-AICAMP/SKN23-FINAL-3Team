# -*- coding: utf-8 -*-
"""
routers/diary_photo_router.py
------------------------------
POST /api/diary/photo-style

사진 업로드 -> 분석(GPT-4o Vision 또는 YOLO+VLM) -> gpt-image-1 그림체 변환 -> S3 업로드 -> URL 반환.

USE_YOLO_PIPELINE=true  → YOLO 객체검출 + Qwen2.5-VL 분석
USE_YOLO_PIPELINE=false → GPT-4o Vision 분석 (기본값)

응답 형식:
  실패: { "type": "bot_text",    "content": "..." }
  성공: { "type": "image_diary", "content": "...", "image_url": "..." }
"""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from openai import AsyncOpenAI
from pydantic import BaseModel

from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ── OpenAI client singleton ───────────────────────────────────────────────────

_openai_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# ── 응답 모델 ─────────────────────────────────────────────────────────────────

class PhotoStyleResponse(BaseModel):
    type: str          # "bot_text" | "image_diary"
    content: str
    image_url: Optional[str] = None


# ── 허용 MIME ─────────────────────────────────────────────────────────────────

_ALLOWED_MIME = {"image/jpeg", "image/jpg", "image/png", "image/webp"}

_BOT_FAIL_MSG  = "강아지나 사람이 있는 실제 사진을 올려주세요!"
_BOT_OK_MSG    = "사진을 그림일기 스타일로 변환했어요!"


# ── Vision 분석 프롬프트 ──────────────────────────────────────────────────────

_VISION_ANALYSIS_PROMPT = """\
Analyze this image and return ONLY a valid JSON object with these exact fields:
- is_real_photo (bool): true if this is a real photograph taken with a camera; false if AI-generated art, illustration, cartoon, screenshot, or CGI
- dog_count (int): exact number of dogs visible in the image (0 if none)
- dog_visual_descriptions (list of str): one concise English description per dog — fur color, coat length/texture, body size, ear shape, any distinctive markings (max 20 words each; empty list if no dogs)
- has_person (bool): true if at least one person is visible
- person_count (int): exact number of people visible (0 if none)
- person_visual_descriptions (list of str): one concise English description per person — clothing colors, rough appearance, hair (max 15 words each; empty list if no people)
- scene_description (str): brief English description of the scene and what subjects are doing (max 20 words)

Return ONLY valid JSON. No markdown fences, no extra explanation."""


async def _analyze_with_vision(image_bytes: bytes, content_type: str) -> dict:
    """GPT-4o Vision으로 이미지 분석: 강아지/사람 감지 + 외형 묘사."""
    client = _get_client()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{content_type};base64,{b64}"

    response = await client.chat.completions.create(
        model=settings.GPT_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url, "detail": "low"}},
                {"type": "text", "text": _VISION_ANALYSIS_PROMPT},
            ],
        }],
        max_tokens=700,
    )

    raw = (response.choices[0].message.content or "{}").strip()
    # JSON 블록 추출 (마크다운 펜스 무시)
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
    try:
        return json.loads(raw)
    except Exception:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {}


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.post(
    "/photo-style",
    response_model=PhotoStyleResponse,
    summary="사진 -> 그림일기 스타일 변환",
    tags=["AI Diary"],
)
async def photo_style(
    file: UploadFile = File(...),
    chat_room_id: Optional[int] = Form(default=None),  # noqa: ARG001 (향후 채팅방 저장용)
    dog_id: Optional[int] = Form(default=None),         # noqa: ARG001 (향후 반려견 정보 보완용)
) -> PhotoStyleResponse:
    """
    사진을 그림일기 일러스트 스타일로 변환합니다.

    - 강아지만 있는 사진 → 강아지만 그림으로 변환
    - 사람만 있는 사진 → 사람만 그림으로 변환
    - 강아지 + 사람 → 함께 그림으로 변환
    - 강아지 여러 마리 → 각각의 외형에 맞게 변환

    실패 시 HTTP 200 + { type: "bot_text" } 반환 (이미지 생성 호출 없음).
    """
    # 1. 파일 타입 검증
    content_type = (file.content_type or "").lower()
    if content_type not in _ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="jpg, png, webp 형식의 사진만 업로드할 수 있어요.",
        )

    # 2. 파일 크기 검증
    image_bytes = await file.read()
    max_bytes = settings.PHOTO_UPLOAD_MAX_MB * 1024 * 1024
    if len(image_bytes) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"파일 크기는 {settings.PHOTO_UPLOAD_MAX_MB}MB 이하로 올려주세요.",
        )

    # 3. 이미지 분석 — YOLO+VLM 또는 GPT-4o Vision
    from services.photo_illustration_service import build_photo_illustration_prompt

    if settings.USE_YOLO_PIPELINE:
        # ── YOLO + VLM 파이프라인 ──────────────────────────────────────────
        from services.photo_detector import detect as yolo_detect
        from services.photo_vlm_service import analyze as vlm_analyze
        from services.photo_validation_service import validate as photo_validate

        logger.info("[photo_style] YOLO+VLM 파이프라인 사용")

        try:
            detection = await yolo_detect(image_bytes)
        except Exception as e:
            logger.error(f"[photo_style] YOLO 검출 실패: {e}")
            return PhotoStyleResponse(type="bot_text", content=_BOT_FAIL_MSG)

        try:
            vlm_result = await vlm_analyze(image_bytes, content_type)
        except Exception as e:
            logger.error(f"[photo_style] VLM 분석 실패: {e}")
            vlm_result = None

        validation = photo_validate(detection, vlm_result)

        if not validation.is_valid:
            logger.info(f"[photo_style] YOLO+VLM 검증 실패: {validation.rejection_reason}")
            return PhotoStyleResponse(type="bot_text", content=_BOT_FAIL_MSG)

        dog_count = validation.dog_count
        has_person = validation.has_person
        scene_description = validation.scene_description
        dog_descs = validation.dog_visual_descriptions
        person_visual_desc = validation.person_visual_description

        image_prompt = build_photo_illustration_prompt(
            dog_count=dog_count,
            has_person=has_person,
            scene_description=scene_description,
            dog_visual_descriptions=dog_descs,
            person_visual_description=person_visual_desc,
        )

    else:
        # ── GPT-4o Vision 파이프라인 (기본) ────────────────────────────────
        logger.info("[photo_style] GPT-4o Vision 파이프라인 사용")

        try:
            vision_data = await _analyze_with_vision(image_bytes, content_type)
        except Exception as e:
            logger.error(f"[photo_style] Vision 분석 실패: {e}")
            return PhotoStyleResponse(type="bot_text", content=_BOT_FAIL_MSG)

        is_real_photo = bool(vision_data.get("is_real_photo", True))
        dog_count = max(0, int(vision_data.get("dog_count", 0)))
        has_person = bool(vision_data.get("has_person", False))
        person_count = max(0, int(vision_data.get("person_count", 0)))
        dog_descs = [str(d) for d in vision_data.get("dog_visual_descriptions", [])]
        person_descs = [str(p) for p in vision_data.get("person_visual_descriptions", [])]
        scene_description = str(vision_data.get("scene_description", ""))

        logger.info(
            f"[photo_style] Vision 결과: real={is_real_photo} dogs={dog_count} persons={person_count}"
        )

        if not is_real_photo or (dog_count == 0 and person_count == 0):
            logger.info(f"[photo_style] 검증 실패: real={is_real_photo} dogs={dog_count} persons={person_count}")
            return PhotoStyleResponse(type="bot_text", content=_BOT_FAIL_MSG)

        has_person = person_count > 0

        person_visual_desc = person_descs[0] if person_descs else ""
        image_prompt = build_photo_illustration_prompt(
            dog_count=dog_count,
            has_person=has_person,
            scene_description=scene_description,
            dog_visual_descriptions=dog_descs,
            person_visual_description=person_visual_desc,
            person_count=person_count,
            person_visual_descriptions=person_descs,
        )

    # 6. gpt-image-1 이미지 생성
    try:
        img_response = await _get_client().images.generate(
            model=settings.GPT_IMAGE_MODEL,
            prompt=image_prompt,
            size="1024x1024",
            quality="medium",
            n=1,
        )
    except Exception as e:
        logger.error(f"[photo_style] 이미지 생성 실패: {e}")
        raise HTTPException(status_code=500, detail="이미지 생성 중 오류가 발생했어요.")

    b64 = img_response.data[0].b64_json
    if not b64:
        raise HTTPException(status_code=500, detail="이미지 생성 결과가 비어 있어요.")

    # 7. S3 업로드
    from services.image_service import _upload_to_s3

    try:
        img_bytes = base64.b64decode(b64)
        image_url = await _upload_to_s3(img_bytes, "photo_style.png", "image/png")
    except Exception as e:
        logger.error(f"[photo_style] S3 업로드 실패: {e}")
        raise HTTPException(status_code=502, detail="이미지 저장 중 오류가 발생했어요.")

    return PhotoStyleResponse(
        type="image_diary",
        content=_BOT_OK_MSG,
        image_url=image_url,
    )
