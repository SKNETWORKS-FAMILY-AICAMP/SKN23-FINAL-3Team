# -*- coding: utf-8 -*-
"""
services/photo_detector.py
--------------------------
YOLOv8n 기반 강아지/사람 객체 검출 서비스.

- 첫 호출 시 모델을 lazy load (singleton).
- USE_YOLO_DETECTOR=false 또는 PHOTO_STYLE_MOCK_MODE=true 이면 mock 반환.
- ultralytics 미설치 시 자동으로 mock 모드 전환.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# ultralytics 없으면 mock 모드 강제
try:
    from ultralytics import YOLO as _YOLO_CLS
    _ULTRALYTICS_AVAILABLE = True
except ImportError:
    _ULTRALYTICS_AVAILABLE = False
    logger.warning("[PhotoDetector] ultralytics 미설치 — mock 모드로 동작합니다.")

# COCO 클래스 ID
_CLS_PERSON = 0
_CLS_DOG = 16

_model: Optional[object] = None


def _get_model():
    """YOLOv8n 모델 singleton. 첫 호출 시 yolov8n.pt 자동 다운로드."""
    global _model
    if _model is None:
        logger.info("[PhotoDetector] YOLOv8n 모델 로드 중...")
        _model = _YOLO_CLS("yolov8n.pt")
        logger.info("[PhotoDetector] 모델 로드 완료")
    return _model


@dataclass
class DetectionResult:
    has_dog: bool
    has_person: bool
    dog_count: int
    person_count: int
    raw_labels: list = field(default_factory=list)


def _detect_sync(image_bytes: bytes) -> DetectionResult:
    """동기 YOLO 추론. run_in_executor로 호출."""
    import io
    from PIL import Image as PILImage

    img = PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    model = _get_model()
    results = model(img, verbose=False, classes=[_CLS_PERSON, _CLS_DOG])

    dog_count = 0
    person_count = 0
    raw_labels: list[str] = []

    for r in results:
        for cls_id in r.boxes.cls.tolist():
            cls_id = int(cls_id)
            if cls_id == _CLS_DOG:
                dog_count += 1
                raw_labels.append("dog")
            elif cls_id == _CLS_PERSON:
                person_count += 1
                raw_labels.append("person")

    return DetectionResult(
        has_dog=dog_count > 0,
        has_person=person_count > 0,
        dog_count=dog_count,
        person_count=person_count,
        raw_labels=raw_labels,
    )


_MOCK_RESULT = DetectionResult(
    has_dog=True,
    has_person=True,
    dog_count=1,
    person_count=1,
    raw_labels=["dog", "person"],
)


async def detect(image_bytes: bytes) -> DetectionResult:
    """
    이미지에서 강아지/사람을 검출합니다.

    USE_YOLO_DETECTOR=false / PHOTO_STYLE_MOCK_MODE=true / ultralytics 미설치
    → mock 결과 반환 (has_dog=True, has_person=True).
    """
    from core.config import settings

    if settings.PHOTO_STYLE_MOCK_MODE:
        logger.debug("[PhotoDetector] mock 모드 — 검출 생략")
        return _MOCK_RESULT

    if not settings.USE_YOLO_DETECTOR:
        logger.debug("[PhotoDetector] USE_YOLO_DETECTOR=false — mock 반환")
        return _MOCK_RESULT

    if not _ULTRALYTICS_AVAILABLE:
        logger.warning("[PhotoDetector] ultralytics 없음 — mock 반환")
        return _MOCK_RESULT

    try:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _detect_sync, image_bytes)
    except Exception as e:
        logger.error(f"[PhotoDetector] 추론 실패: {e}")
        raise
