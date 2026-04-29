# -*- coding: utf-8 -*-
"""
ai/retrievers/query_parser.py
-----------------------------
사용자 쿼리를 RDB 필터용 객관 조건 / ChromaDB 검색용 주관 조건으로 분리.

예)
  입력: "잠실 주말에 강아지랑 갈 수 있는 조용한 카페"
  출력: {
    "city":           null,
    "district":       "송파구",
    "sub_category":   "카페",
    "is_indoor":      null,
    "is_outdoor":     null,
    "has_parking":    null,
    "pet_zone_type":  null,
    "pet_size_limit": null,
    "time_condition": "주말",
    "landmark":       null,
    "subjective":     "조용한 분위기"
  }
"""

from __future__ import annotations

import json
import logging

from openai import AsyncOpenAI
from back.api.core.config import settings

logger = logging.getLogger(__name__)

_PARSE_SYSTEM = """\
반려견 장소 검색 쿼리를 분석해서 아래 JSON 형식으로만 반환하세요. 설명 없이 JSON만 출력하세요.

[필드 설명]
- city: 광역시/도 전체 명칭 (예: "서울특별시", "경기도", "부산광역시") — 언급 없으면 null
- district: 반드시 행정구역 '구/군' 단위 명칭으로 반환하세요 (예: "강남구", "마포구").
  동네명·상권명은 해당 구 이름으로 변환해야 합니다:
    잠실 → 송파구, 홍대/홍익대 → 마포구, 이태원 → 용산구,
    신촌/연희동 → 서대문구, 연남동/망원/합정 → 마포구, 압구정/청담 → 강남구, 건대/건국대 → 광진구,
    신림 → 관악구, 수유/쌍문 → 도봉구, 노원 → 노원구, 상계 → 노원구,
    종로/북촌/경복궁 → 종로구, 명동/을지로/남대문 → 중구,
    여의도 → 영등포구, 목동 → 양천구, 강서 → 강서구, 분당 → 분당구,
    일산 → 일산동구, 판교 → 수정구, 수원 → 팔달구, 성수동 → 성동구
  위 예시에 없는 지역도 당신의 지식으로 올바른 구 이름을 추론하세요.
  구 이름이 확실하지 않으면 null을 반환하세요.
  ※ landmark 필드에 들어갈 구체적 장소(경복궁, 한강공원 등)는 district가 아니라 landmark에 넣으세요.
- sub_category: 아래 목록 중 하나만 정확히 반환하세요. 없으면 null
    카페         → 반려견 카페, 애견카페, 커피숍
    식당         → 음식점, 맛집, 레스토랑, 식당
    펜션         → 펜션, 숙박, 게스트하우스, 글램핑
    호텔         → 호텔
    공원         → 공원, 산책로, 한강공원
    반려견놀이터 → 놀이터, 애견 운동장
    관광지       → 관광지, 명소, 전망대
    동물병원     → 동물병원, 수의사, 동물 응급
    동물약국     → 동물약국, 반려동물 약국
    반려동물용품 → 펫샵, 애견용품점, 반려동물 용품
    미용         → 애견미용, 그루밍, 펫미용
    위탁관리     → 펫시터, 펫호텔, 위탁, 데이케어
    박물관       → 박물관, 미술관, 전시관
- is_indoor: 실내 공간 요청이면 true, 실외 요청이면 false, 언급 없으면 null
- is_outdoor: 실외 공간 요청이면 true, 실내 요청이면 false, 언급 없으면 null
- has_parking: 주차 필요하면 "Y", 불필요하면 "N", 언급 없으면 null
- pet_zone_type: "전구역"/"실내구역"/"실외구역" 중 하나, 언급 없으면 null
- pet_size_limit: "소형"/"중형"/"대형" 중 하나, 반려견 크기를 말할 때만 사용. 장소 규모(예: "대형 카페", "넓은 카페")는 subjective로 보내고 pet_size_limit에는 넣지 말 것
- entrance_fee_preference: 입장료/이용료 조건. "입장료 없이", "무료 입장"이면 "free_only", 아니면 null
- extra_fee_preference: 반려견 동반 추가요금 조건. "추가 비용 없이", "추가요금 없는", "강아지 추가요금 없음"이면 "no_extra_fee", 아니면 null
- time_condition: 시간/요일 조건. 아래 값 중 하나, 없으면 null
    "이른아침" → 오전 일찍, 아침 일찍, 이른 아침 (09시 이전 오픈)
    "오전"     → 오전에, 아침에 (10시 이전 오픈)
    "점심"     → 점심시간에, 낮에
    "저녁"     → 저녁에, 저녁 이후
    "밤"       → 밤 늦게, 늦은 시간, 야간 (22시 이후까지 영업)
    "주말"     → 주말에, 이번 주말, 토요일, 일요일
    "공휴일"   → 공휴일, 연휴, 법정공휴일에도 영업
    "연중무휴" → 연중무휴, 365일 영업, 쉬는 날 없는
    "24시간"   → 24시간, 하루종일 오픈, 밤새 영업, 새벽까지
- landmark: "근처", "주변", "앞", "옆" 표현과 함께 언급된 장소명 또는 지역명. 없으면 null
  POI 뿐만 아니라 동네명도 포함됩니다:
    "경복궁 근처"  → landmark: "경복궁",  district: null
    "용산 근처"    → landmark: "용산",    district: null
    "강남역 주변"  → landmark: "강남역",  district: null
    "한강공원 근처" → landmark: "한강공원", district: null
  ※ "근처/주변/앞/옆" 없이 단순 지역 언급이면 district로 처리 ("용산구에서" → district: "용산구")
- subjective: 위 조건에 해당하지 않는 분위기·특성 (예: "조용한", "넓은 야외", "아늑한", "뷰 좋은"). 없으면 빈 문자열

[출력 형식]
{
  "city": null,
  "district": null,
  "sub_category": null,
  "is_indoor": null,
  "is_outdoor": null,
  "has_parking": null,
  "pet_zone_type": null,
  "pet_size_limit": null,
  "entrance_fee_preference": null,
  "extra_fee_preference": null,
  "waste_bag_preference": null,
  "time_condition": null,
  "landmark": null,
  "subjective": ""
}

For waste-bag requests:
- "배변봉투 안 챙기고", "배변봉투 없이", "배변봉투 제공", "배변봉투 비치" -> set waste_bag_preference to "provided_or_not_required"
"""


class QueryParser:
    """LLM으로 사용자 쿼리를 객관/주관 조건으로 분리한다."""

    def __init__(self, llm_client: AsyncOpenAI, model: str | None = None):
        self._llm   = llm_client
        self._model = model or settings.GPT_MODEL

    async def parse(self, query: str) -> dict:
        """쿼리를 파싱해서 조건 dict 반환. 실패 시 subjective=query만 담아 반환."""
        try:
            resp = await self._llm.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": _PARSE_SYSTEM},
                    {"role": "user",   "content": query},
                ],
                temperature=0,
                max_tokens=300,
            )
            raw = resp.choices[0].message.content.strip()
            raw = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(raw)
            logger.info(f"[QueryParser] 파싱 완료: {result}")
            return result
        except Exception as e:
            logger.warning(f"[QueryParser] 파싱 실패, 원문 사용: {e}")
            return {"subjective": query}
