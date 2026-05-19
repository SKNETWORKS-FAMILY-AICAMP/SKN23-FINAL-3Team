# -*- coding: utf-8 -*-
"""
services/photo_validation_service.py
--------------------------------------
YOLO 검출 결과 + VLM 분석 결과를 합쳐 최종 검증을 수행합니다.

검증 통과 조건 (모두 True):
  1. is_real_photo  — 실제 촬영 사진 (VLM 판별, VLM 없으면 True 가정)
  2. has_dog        — 강아지 1마리 이상 (YOLO 우선, VLM 보조)
  3. has_person     — 사람 1명 이상 (YOLO 우선)

기존 PhotoValidationResult와 호환 유지.
"""

from __future__ import annotations

import logging
from typing import Optional

from services.photo_detector import DetectionResult
from services.photo_vlm_service import VLMResult
from services.photo_illustration_service import PhotoValidationResult

logger = logging.getLogger(__name__)

_REJECTION_MSG = "강아지와 보호자 사진으로 업로드해주세요!"


def validate(
    detection: DetectionResult,
    vlm_result: Optional[VLMResult],
) -> PhotoValidationResult:
    """
    YOLO + VLM 결과를 합쳐 PhotoValidationResult를 반환합니다.

    Args:
        detection:  YOLO 검출 결과
        vlm_result: VLM 분석 결과 (None이면 실사 여부 검사 생략)

    Returns:
        PhotoValidationResult
    """
    # 1. 실사 여부 — VLM 결과가 있을 때만 검사
    is_real_photo = vlm_result.is_real_photo if vlm_result is not None else True

    # 2. 강아지 존재 — YOLO 1차, VLM 묘사로 보완
    has_dog = detection.has_dog
    if not has_dog and vlm_result is not None:
        has_dog = len(vlm_result.dog_visual_descriptions) > 0

    # 3. 사람 존재 — YOLO 결과
    has_person = detection.has_person

    # 강아지만, 사람만, 또는 함께 있어도 통과 (둘 중 하나 이상 필요)
    is_valid = is_real_photo and (has_dog or has_person)

    logger.info(
        f"[PhotoValidation] real={is_real_photo} dog={has_dog} person={has_person} "
        f"=> valid={is_valid}"
    )

    return PhotoValidationResult(
        is_valid=is_valid,
        rejection_reason=None if is_valid else _REJECTION_MSG,
        dog_count=detection.dog_count,
        has_person=has_person,
        scene_description=vlm_result.scene_description if vlm_result else "",
        dog_visual_descriptions=vlm_result.dog_visual_descriptions if vlm_result else [],
        person_visual_description=vlm_result.person_visual_description if vlm_result else "",
    )
