# ai/llm/rag/context_builder.py
# 검색 결과 → GPT 프롬프트 컨텍스트 구성

from ai.llm.rag.breed_retriever import get_breed_context
from ai.llm.rag.diary_retriever import search_similar_diaries, format_past_diaries
from ai.llm.rag.places_retriever import search_similar_places, format_places_context


def build_diary_context(
    breed_name: str,
    user_id: str,
    today_activity: str,
) -> dict:
    """
    일기 생성용 컨텍스트 구성
    → breed_retriever + diary_retriever 검색 결과를 GPT 프롬프트에 넣을 형태로 조합

    Parameters:
        breed_name: 영문 견종명 (소문자, 예: "pomeranian")
        user_id: 사용자 ID (과거 일기 검색용)
        today_activity: 오늘 활동 텍스트 (예: "한강에서 산책했어요")

    Returns:
        {
            "breed_context": {
                "breed_name_ko": "포메라니안",
                "activity_level": "medium",
                "temperament": "활발한, 호기심 많은, ...",
                "document": "포메라니안은 활발하고..."
            },
            "past_diaries_text": "[2026-04-10 / 한강공원]\n오늘 한강에서...",
            "has_past_diaries": True
        }
    """
    # 1. 견종 성격 컨텍스트 검색
    breed_context = get_breed_context(breed_name)

    # 2. 유사 과거 일기 검색
    past_diaries = search_similar_diaries(
        user_id=user_id,
        query_text=today_activity,
        n_results=3,
    )

    # 3. 과거 일기 텍스트 변환
    past_diaries_text = format_past_diaries(past_diaries)

    return {
        "breed_context": breed_context,
        "past_diaries_text": past_diaries_text,
        "has_past_diaries": len(past_diaries) > 0,
    }


def build_places_context(
    query_text: str,
    category: str = None,
    city: str = None,
    n_results: int = 5,
) -> dict:
    """
    장소 추천용 컨텍스트 구성
    → places_retriever 검색 결과를 GPT 프롬프트에 넣을 형태로 조합

    Parameters:
        query_text: 검색 쿼리 (예: "한강이랑 비슷한 넓은 공원")
        category: 카테고리 필터 (선택)
        city: 도시 필터 (선택)
        n_results: 반환할 장소 수 (기본 5개)

    Returns:
        {
            "places": [...],            # 장소 목록 (지도 마커용)
            "places_text": "...",       # 프롬프트용 텍스트
            "has_places": True
        }
    """
    # 유사 장소 검색
    places = search_similar_places(
        query_text=query_text,
        n_results=n_results,
        category=category,
        city=city,
    )

    # 장소 텍스트 변환
    places_text = format_places_context(places)

    return {
        "places": places,               # 지도 마커 표시용
        "places_text": places_text,     # GPT 프롬프트 주입용
        "has_places": len(places) > 0,
    }