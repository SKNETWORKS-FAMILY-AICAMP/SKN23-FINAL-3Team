# ai/llm/chains/places_chain.py
# 장소 추천 파이프라인
# RAG 검색 → 성향 점수 보정 → GPT 자연어 설명 생성

import json
from openai import OpenAI
from dotenv import load_dotenv

from ai.llm.rag.context_builder import build_places_context
from ai.llm.prompts.places_prompt import PLACES_SYSTEM_PROMPT, build_places_prompt
from ai.utils.scoring import (
    classify_dog_type,
    classify_owner_type,
    calculate_dog_score_vector,
    get_type_name,
)

load_dotenv()

client = OpenAI()
MODEL = "gpt-4.1-mini"


def rerank_places(places: list, dog_score_vector: dict) -> list:
    """
    ChromaDB 유사도 점수 + 반려견 성향 벡터 보정으로 재순위

    반려견 성향 보정 규칙:
    - 자극민감도(e) 높음 → 실외 장소 감점, 조용한 곳 가점
    - 활동성(a) 높음 → 공원/놀이터 가점
    - 사회성(b) 높음 → 카페/관광지 가점

    Parameters:
        places: places_retriever 결과 목록
        dog_score_vector: calculate_dog_score_vector() 결과

    Returns:
        재순위된 장소 목록
    """
    a = dog_score_vector.get("a", 0)  # 활동성
    b = dog_score_vector.get("b", 0)  # 사회성
    e = dog_score_vector.get("e", 0)  # 자극민감도

    for place in places:
        bonus = 0
        category = place.get("category", "")
        outdoor = place.get("outdoor", "N")

        # 자극민감도 높음 → 실외 장소 감점
        if e > 3 and outdoor == "Y":
            bonus -= 0.1

        # 활동성 높음 → 공원/놀이터 가점
        if a > 3 and category in ["공원", "놀이터"]:
            bonus += 0.1

        # 사회성 높음 → 카페/관광지 가점
        if b > 3 and category in ["카페", "관광지"]:
            bonus += 0.05

        place["final_score"] = round(place.get("similarity", 0) + bonus, 4)

    # final_score 기준 내림차순 정렬
    return sorted(places, key=lambda x: x.get("final_score", 0), reverse=True)


def run_places_chain(
    pet_name: str,
    dog_tags: list,
    owner_tags: list,
    user_query: str = "",
    category: str = None,
    city: str = None,
    n_results: int = 5,
) -> dict:
    """
    장소 추천 전체 파이프라인 실행

    Parameters:
        pet_name: 강아지 이름
        dog_tags: 반려견 성격 태그 목록
        owner_tags: 보호자 라이프스타일 태그 목록
        user_query: 사용자 추가 질문 (선택)
        category: 카테고리 필터 (선택)
        city: 도시 필터 (선택)
        n_results: 추천 장소 수 (기본 5개)

    Returns:
        {
            "message": "GPT 자연어 추천 메시지",
            "places": [
                {
                    "name": "평화의 공원",
                    "reason": "추천 이유",
                    "address": "서울특별시...",
                    "lat": 37.5765,
                    "lng": 126.9186,
                    ...
                }
            ],
            "dog_type": "d_c",
            "dog_type_name": "🌙 조심스러운 아이",
            "owner_type": "o_a",
            "owner_type_name": "🌿 자연 애호가",
        }
    """
    # 1. 타입 분류
    dog_type = classify_dog_type(dog_tags)
    owner_type = classify_owner_type(owner_tags)
    dog_type_name = get_type_name(dog_type)
    owner_type_name = get_type_name(owner_type)

    print(f"반려견 타입: {dog_type_name}")
    print(f"보호자 타입: {owner_type_name}")

    # 2. 보호자 성향 기반 쿼리 생성
    # 보호자 태그를 자연어 쿼리로 변환해서 ChromaDB 검색
    owner_query = user_query if user_query else " ".join(owner_tags)

    # 3. RAG 장소 검색
    context = build_places_context(
        query_text=owner_query,
        category=category,
        city=city,
        n_results=n_results,
    )

    if not context["has_places"]:
        return {
            "message": f"{pet_name}와 함께 갈 수 있는 장소를 찾지 못했어요. 다른 조건으로 검색해보세요 🐾",
            "places": [],
            "dog_type": dog_type,
            "dog_type_name": dog_type_name,
            "owner_type": owner_type,
            "owner_type_name": owner_type_name,
        }

    # 4. 반려견 성향 벡터 보정 (재순위)
    dog_score_vector = calculate_dog_score_vector(dog_tags)
    reranked_places = rerank_places(context["places"], dog_score_vector)

    # 5. 프롬프트 구성
    # 재순위된 장소로 텍스트 재구성
    from ai.llm.rag.places_retriever import format_places_context
    places_text = format_places_context(reranked_places)

    user_prompt = build_places_prompt(
        pet_name=pet_name,
        dog_type_name=dog_type_name,
        owner_type_name=owner_type_name,
        dog_tags=dog_tags,
        owner_tags=owner_tags,
        places_text=places_text,
        user_query=user_query,
    )

    # 6. GPT 호출
    print("GPT 장소 추천 생성 중...")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PLACES_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=1000,
        temperature=0.7,
    )

    raw = response.choices[0].message.content.strip()

    # 7. JSON 파싱
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        result = json.loads(clean)
    except Exception as e:
        print(f"JSON 파싱 오류: {e}")
        result = {"message": raw, "places": []}

    # 8. 장소 메타데이터 병합 (지도 마커용)
    result_places = []
    gpt_places = {p["name"]: p.get("reason", "") for p in result.get("places", [])}

    for place in reranked_places:
        name = place.get("name", "")
        result_places.append({
            **place,
            "reason": gpt_places.get(name, ""),
        })

    return {
        "message": result.get("message", ""),
        "places": result_places,
        "dog_type": dog_type,
        "dog_type_name": dog_type_name,
        "owner_type": owner_type,
        "owner_type_name": owner_type_name,
    }