# -*- coding: utf-8 -*-
"""
ai/retrievers/facility_query_parser.py
--------------------------------------
시설정보 의도(`시설정보`) 전용 LLM 쿼리 파서.

장소추천용 `QueryParser` 가 객관(필터)/주관(분위기) 분리를 목적으로 하는
풀 프롬프트(80+ 줄)인 것과 달리, 본 파서는 시설정보 핸들러가 단일 시설을
정확히 찾기 위해 필요한 두 슬롯만 추출한다.

추출 슬롯:
    - facility_name: 사용자가 호명한 시설명/상호명 (없으면 null).
    - city         : "서울" / 그 외 지역명 / null. 서울 외 지역 차단에 사용.

예)
    "용산 드로우지 주차 가능해?"  -> {"facility_name": "드로우지", "city": "서울"}
    "스타벅스 강남점 영업시간"     -> {"facility_name": "스타벅스 강남점", "city": "서울"}
    "한강공원 운영시간"            -> {"facility_name": "한강공원", "city": "서울"}
    "부산 해운대 카페 추천"        -> {"facility_name": null, "city": "부산"}
"""

from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI

from back.api.core.config import settings

logger = logging.getLogger(__name__)

_FACILITY_PARSE_SYSTEM = """\
사용자 발화에서 다음 두 필드만 JSON으로 추출하라. 설명 없이 JSON만 출력하라.

[필드]
- facility_name: 사용자가 호명한 **시설명/상호명/고유 장소명**.
  근처/주변/앞/옆 같은 위치 표현 없이 직접 호명한 경우도 그대로 추출하라.
  여러 단어로 구성된 상호명은 통째로 묶어라(예: "스타벅스 강남점").
  지역명·구·동·시는 facility_name 이 아니다(그건 city 또는 무시).
  시설명이 없으면 null.

  예)
    "용산 드로우지 주차 가능해?"   -> "드로우지"   (용산은 city)
    "스타벅스 강남점 영업시간"      -> "스타벅스 강남점"
    "한강공원 운영시간"             -> "한강공원"
    "이태원 해방촌 더피커 카페"     -> "더피커"     (이태원·해방촌은 위치 컨텍스트)
    "강아지 갈만한 카페 추천"        -> null         (시설 호명 없음)
    "용산 근처 카페"                -> null         (시설 호명 없음, 카테고리 추천)

- city: 발화에 명시된 광역 도시. "서울" 또는 그 외 도시명("부산", "대구" 등).
  서울 자치구(용산·강남·종로·마포 등)·동네명이 언급되면 city 는 "서울".
  도시 언급이 없으면 null.

  예)
    "용산 드로우지 ..."     -> "서울"
    "강남역 근처 ..."        -> "서울"
    "부산 해운대 ..."        -> "부산"
    "강아지 카페 추천"       -> null

[출력 형식]
{"facility_name": null, "city": null}
"""


class FacilityQueryParser:
    """시설정보 전용 LLM 파서. facility_name + city 두 슬롯만 추출한다."""

    def __init__(self, llm_client: AsyncOpenAI, model: str | None = None) -> None:
        self._llm = llm_client
        self._model = model or settings.GPT_MODEL

    async def parse(self, query: str) -> dict:
        """발화를 파싱해 `{facility_name, city}` 반환.

        Args:
            query: 사용자 발화 원문.

        Returns:
            `{"facility_name": str | None, "city": str | None}` 형태의 dict.
            LLM 호출 실패 시 두 필드 모두 None 으로 안전하게 반환.
        """
        try:
            resp = await self._llm.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _FACILITY_PARSE_SYSTEM},
                    {"role": "user", "content": query},
                ],
                temperature=0,
                max_tokens=80,
            )
            raw = resp.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)

            facility_name = result.get("facility_name")
            city = result.get("city")
            if isinstance(facility_name, str):
                facility_name = facility_name.strip() or None
            if isinstance(city, str):
                city = city.strip() or None

            normalized = {"facility_name": facility_name, "city": city}
            logger.info(f"[FacilityQueryParser] 파싱 완료: {normalized}")
            return normalized
        except Exception as e:
            logger.warning(f"[FacilityQueryParser] 파싱 실패, 빈 결과 반환: {e}")
            return {"facility_name": None, "city": None}
