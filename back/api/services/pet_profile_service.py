# -*- coding: utf-8 -*-
"""
services/pet_profile_service.py
-------------------------------
반려견 사진 → GPT-4o Vision 분석 → pet_profiles 테이블 UPSERT.

일기 그림 생성 시 english_prompt / must_include_keywords 를 활용하여
매번 동일한 외형의 반려견 일러스트를 재현.
"""

from __future__ import annotations

import base64
import json
import logging
import re
from typing import Optional

import httpx
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.utils import kst_now
from models.image import Image
from models.pet_profile import PetProfile

logger = logging.getLogger(__name__)

# ── OpenAI 클라이언트 (diary_photo_router.py 동일 패턴) ─────────────────────

_openai_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


# ── 분석 프롬프트 ────────────────────────────────────────────────────────────

_PET_PROFILE_PROMPT = """\
이 사진은 사용자가 등록한 반려동물의 프로필 사진입니다.
견종·이름·생년월일 등 기본 정보는 이미 별도로 관리되고 있습니다.

이 분석의 목적은 **사진에서만 알 수 있는 시각적 외형 정보**(털 색·질감, 눈 색, 귀 모양, 특이 표식 등)를 추출하여
일기 그림을 생성할 때 매번 동일한 외형으로 재현하는 것입니다.

업로드된 사진을 자세히 관찰한 뒤, 아래 JSON 형식으로만 응답하세요.

{
  "is_pet_detected": boolean,
  "species": "dog" | "cat" | "other" | null,

  "fur": {
    "primary_color": "주 색상을 구체적으로 (예: '크림 베이지', '검정에 가까운 초콜릿 브라운')",
    "secondary_colors": ["부 색상 배열, 없으면 빈 배열"],
    "pattern": "솔리드 | 투톤 | 삼색 | 얼룩 | 브린들 | 점박이 등",
    "length": "short" | "medium" | "long",
    "texture": "직모 | 곱슬 | 웨이브 | 와이어 | 더블코트"
  },

  "face": {
    "eye_color": "구체적 색상 (예: '진한 갈색', '호박색', '하늘색')",
    "eye_shape": "둥근 | 아몬드 | 처진 | 또렷한",
    "nose_color": "검정 | 분홍 | 갈색 등",
    "mouth_notes": "특이사항 (혀가 자주 보임, 아랫턱 돌출 등). 없으면 null"
  },

  "ears": {
    "shape": "쫑긋 선 | 반쫑긋 | 늘어진 | 짧은 | 자른",
    "size": "small" | "medium" | "large"
  },

  "tail": "말린 | 곧은 | 풍성한 | 짧은 | 보이지 않음",

  "distinctive_markings": [
    "동일한 외형 재현에 꼭 필요한 시각적 단서만 (예: '가슴에 V자 흰털', '네 발 끝 흰 양말', '왼쪽 눈 위 검은 점')"
  ],

  "vibe": "외형에서 풍기는 인상 한 줄 (예: '장난기 많고 활발해 보임')",

  "image_quality_notes": "분석에 영향을 준 조건 (역광, 흐림, 일부 가려짐 등). 없으면 null",

  "character_sheet": {
    "korean_summary": "한 문단으로 정리한 한국어 외형 설명 (그림 작가가 읽고 그릴 수 있는 수준의 구체성). 견종·이름은 제외하고 순수 시각 정보만.",
    "english_prompt": "이미지 생성 모델에 그대로 넣을 수 있는 영문 외형 프롬프트 조각. 견종명은 제외하고 색상·질감·표식 중심 (예: 'cream-colored curly medium-length fur, round dark brown eyes, floppy ears, V-shaped white patch on chest, four white socks, friendly expression')",
    "must_include_keywords": ["일관성을 위해 매 그림 프롬프트에 반드시 포함해야 할 핵심 시각 키워드 3-5개 (견종명 제외, 털색·질감·표식 위주)"]
  }
}

## 분석 원칙

- 색상은 두루뭉술한 단어 금지. '갈색' X → '진한 초콜릿 브라운' O
- distinctive_markings 에는 매번 같은 모습으로 그리기 위해 반드시 필요한 단서만 골라 적습니다
- must_include_keywords 는 영문 프롬프트의 핵심 3-5개만 추출. 주 색상, 털 길이/질감, 가장 두드러진 marking 위주
- 견종명·이름·몸무게는 별도 관리되므로 character_sheet 에 포함하지 마세요
- 사진에 반려동물이 없거나 식별 불가능하면 is_pet_detected: false, 그 외 모든 필드는 null
- JSON 외 다른 텍스트(인사말, 설명, 코드블록 펜스 ```) 절대 출력 금지
- 응답은 유효한 JSON 한 덩어리만"""


async def _analyze_image_with_vision(image_bytes: bytes, content_type: str) -> dict:
    """GPT-4o Vision 으로 반려견 사진 분석 → 구조화된 프로필 JSON 반환."""
    client = _get_client()
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{content_type};base64,{b64}"

    response = await client.chat.completions.create(
        model=settings.GPT_MODEL,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": data_url, "detail": "high"}},
                {"type": "text", "text": _PET_PROFILE_PROMPT},
            ],
        }],
        max_tokens=2000,
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


async def analyze_pet_profile(
    pet_id: int,
    image_id: int,
    db: AsyncSession,
) -> PetProfile:
    """
    반려견 사진을 GPT-4o Vision 으로 분석하고 pet_profiles 에 UPSERT.

    Args:
        pet_id:   반려견 ID
        image_id: 분석할 이미지 ID (images 테이블)
        db:       AsyncSession

    Returns:
        저장된 PetProfile ORM 객체
    """
    # 1) 이미지 URL 조회
    result = await db.execute(
        select(Image).where(Image.id == image_id, Image.deleted_at.is_(None))
    )
    image_row = result.scalar_one_or_none()
    if image_row is None:
        raise ValueError(f"이미지(id={image_id})를 찾을 수 없습니다.")

    file_url: str = image_row.file_url

    # 2) S3 에서 이미지 다운로드
    async with httpx.AsyncClient(timeout=30) as http:
        resp = await http.get(file_url)
        resp.raise_for_status()
        image_bytes = resp.content

    # content-type 추정
    ct = resp.headers.get("content-type", "image/jpeg")

    # 3) GPT-4o Vision 분석
    profile_data = await _analyze_image_with_vision(image_bytes, ct)
    logger.info(f"[PetProfile] pet_id={pet_id} 분석 완료: detected={profile_data.get('is_pet_detected')}")

    # 4) UPSERT — pet_id UNIQUE 이므로 기존 행이 있으면 업데이트
    existing = await db.execute(
        select(PetProfile).where(PetProfile.pet_id == pet_id)
    )
    row = existing.scalar_one_or_none()

    now = kst_now()
    if row is not None:
        row.image_id = image_id
        row.profile_json = profile_data
        row.analyzed_at = now
    else:
        row = PetProfile(
            pet_id=pet_id,
            image_id=image_id,
            profile_json=profile_data,
            analyzed_at=now,
        )
        db.add(row)

    await db.flush()
    return row
