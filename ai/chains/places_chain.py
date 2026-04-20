# -*- coding: utf-8 -*-
import json
from openai import AsyncOpenAI

from ai.core.interfaces.base_chain import BaseChain
from ai.core.interfaces.base_retriever import BaseRetriever
from ai.core.interfaces.base_prompt_builder import BasePromptBuilder
from ai.scorers.dog_scorer import DogScorer
from ai.scorers.owner_scorer import OwnerScorer
from ai.infrastructure.cost_tracker import OpenAICostTracker

MODEL = "gpt-4.1-mini"


class PlacesChain(BaseChain):

    def __init__(
        self,
        retriever: BaseRetriever,
        dog_scorer: DogScorer,
        owner_scorer: OwnerScorer,
        prompt_builder: BasePromptBuilder,
        llm_client: AsyncOpenAI,
        cost_tracker: OpenAICostTracker,
    ):
        self._retriever      = retriever
        self._dog_scorer     = dog_scorer
        self._owner_scorer   = owner_scorer
        self._prompt_builder = prompt_builder
        self._llm            = llm_client
        self._cost_tracker   = cost_tracker

    async def run(
        self,
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

        Returns:
            {
                "message": "GPT 자연어 추천 메시지",
                "places": [...],
                "dog_type": "d_c" or None,
                "dog_type_name": "🌙 조심스러운 아이" or "",
                "owner_type": "o_a" or None,
                "owner_type_name": "🌿 자연 애호가" or "",
            }
        """
        # Step 1. 타입 분류 (태그 있을 때만)
        dog_type       = self._dog_scorer.classify_type(dog_tags)   if dog_tags   else None
        owner_type     = self._owner_scorer.classify_type(owner_tags) if owner_tags else None
        dog_type_name  = self._dog_scorer.get_type_name(dog_type)   if dog_type   else ""
        owner_type_name = self._owner_scorer.get_type_name(owner_type) if owner_type else ""

        if dog_type_name:
            print(f"반려견 타입: {dog_type_name}")
        if owner_type_name:
            print(f"보호자 타입: {owner_type_name}")

        # Step 2. 검색 쿼리 생성
        if user_query:
            owner_query = user_query
        elif owner_tags:
            owner_query = " ".join(owner_tags)
        else:
            owner_query = "반려견 동반 가능한 장소"

        # Step 3. RAG 장소 검색
        places = self._retriever.search(
            query=owner_query,
            n_results=n_results,
            category=category,
            city=city,
        )

        # 예외 처리: 결과 없을 때
        if not places:
            print("장소 검색 결과 없음")
            return {
                "message": "",
                "places": [],
                "dog_type": dog_type,
                "dog_type_name": dog_type_name,
                "owner_type": owner_type,
                "owner_type_name": owner_type_name,
            }

        # Step 4. 반려견 성향 벡터 보정 (재순위) — 태그 있을 때만
        if dog_tags:
            dog_score_vector = self._dog_scorer.calculate_vector(dog_tags)
            reranked_places  = self._rerank(places, dog_score_vector)
        else:
            reranked_places = places

        # Step 5. 프롬프트 구성
        places_text = self._retriever.format_context(reranked_places)

        system_prompt = self._prompt_builder.build_system_prompt()
        user_prompt   = self._prompt_builder.build_user_prompt(
            pet_name=pet_name,
            dog_type_name=dog_type_name,
            owner_type_name=owner_type_name,
            dog_tags=dog_tags,
            owner_tags=owner_tags,
            places_text=places_text,
            user_query=user_query,
        )

        # Step 6. GPT 호출
        print("GPT 장소 추천 생성 중...")
        try:
            response = await self._llm.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            raw = response.choices[0].message.content.strip()
            await self._cost_tracker.track_chat(response, note="places_chain")

        except Exception as e:
            print(f"GPT 호출 오류: {e}")
            return {
                "message": f"{pet_name}에게 맞는 장소를 찾았어요! 아래 목록을 확인해보세요 🐾",
                "places": reranked_places,
                "dog_type": dog_type,
                "dog_type_name": dog_type_name,
                "owner_type": owner_type,
                "owner_type_name": owner_type_name,
            }

        # Step 7. JSON 파싱
        try:
            clean  = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean)
        except Exception as e:
            print(f"JSON 파싱 오류: {e}")
            return {
                "message": raw,
                "places": reranked_places,
                "dog_type": dog_type,
                "dog_type_name": dog_type_name,
                "owner_type": owner_type,
                "owner_type_name": owner_type_name,
            }

        # Step 8. 장소 메타데이터 병합 (지도 마커용)
        gpt_places    = {p["name"]: p.get("reason", "") for p in result.get("places", [])}
        result_places = [
            {**place, "reason": gpt_places.get(place.get("name", ""), "")}
            for place in reranked_places
        ]

        return {
            "message": result.get("message", ""),
            "places": result_places,
            "dog_type": dog_type,
            "dog_type_name": dog_type_name,
            "owner_type": owner_type,
            "owner_type_name": owner_type_name,
        }

    def _rerank(self, places: list, dog_score_vector: dict) -> list:
        """반려견 성향 벡터 보정으로 재순위 (기존 rerank_places() 로직 그대로)"""
        if not places:
            return []

        a = dog_score_vector.get("a", 0)  # 활동성
        b = dog_score_vector.get("b", 0)  # 사회성
        e = dog_score_vector.get("e", 0)  # 자극민감도

        for place in places:
            bonus    = 0
            category = place.get("category", "")
            outdoor  = place.get("outdoor", "N")

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

        return sorted(places, key=lambda x: x.get("final_score", 0), reverse=True)