# -*- coding: utf-8 -*-
import json
import logging

from openai import AsyncOpenAI

from back.api.core.config import settings
from ai.core.interfaces.base_chain import BaseChain
from ai.core.interfaces.base_prompt_builder import BasePromptBuilder
from ai.core.interfaces.base_retriever import BaseRetriever
from ai.infrastructure.cost_tracker import OpenAICostTracker
from ai.scorers.dog_scorer import DogScorer
from ai.scorers.owner_scorer import OwnerScorer

MODEL = settings.GPT_MODEL
logger = logging.getLogger(__name__)


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
        self._retriever = retriever
        self._dog_scorer = dog_scorer
        self._owner_scorer = owner_scorer
        self._prompt_builder = prompt_builder
        self._llm = llm_client
        self._cost_tracker = cost_tracker

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
        """Run the full place recommendation chain."""
        dog_type = self._dog_scorer.classify_type(dog_tags) if dog_tags else None
        owner_type = self._owner_scorer.classify_type(owner_tags) if owner_tags else None
        dog_type_name = self._dog_scorer.get_type_name(dog_type) if dog_type else ""
        owner_type_name = self._owner_scorer.get_type_name(owner_type) if owner_type else ""

        if user_query:
            owner_query = user_query
        elif owner_tags:
            owner_query = " ".join(owner_tags)
        else:
            owner_query = "반려견 동반 가능한 장소"

        places = self._retriever.search(
            query=owner_query,
            n_results=n_results,
            category=category,
            city=city,
        )

        if not places:
            return {
                "message": "",
                "places": [],
                "dog_type": dog_type,
                "dog_type_name": dog_type_name,
                "owner_type": owner_type,
                "owner_type_name": owner_type_name,
            }

        reranked_places = self.rerank_places(
            places,
            dog_tags=dog_tags,
            owner_tags=owner_tags,
        )

        places_text = self._retriever.format_context(reranked_places)
        system_prompt = self._prompt_builder.build_system_prompt()
        user_prompt = self._prompt_builder.build_user_prompt(
            pet_name=pet_name,
            dog_type_name=dog_type_name,
            owner_type_name=owner_type_name,
            dog_tags=dog_tags,
            owner_tags=owner_tags,
            places_text=places_text,
            user_query=user_query,
        )

        try:
            response = await self._llm.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )
            raw = response.choices[0].message.content.strip()
            await self._cost_tracker.track_chat(response, note="places_chain")
        except Exception:
            return {
                "message": f"{pet_name}에게 맞는 장소를 찾았어요! 아래 목록을 확인해보세요.",
                "places": reranked_places,
                "dog_type": dog_type,
                "dog_type_name": dog_type_name,
                "owner_type": owner_type,
                "owner_type_name": owner_type_name,
            }

        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean)
        except Exception:
            return {
                "message": raw,
                "places": reranked_places,
                "dog_type": dog_type,
                "dog_type_name": dog_type_name,
                "owner_type": owner_type,
                "owner_type_name": owner_type_name,
            }

        gpt_places = {p["name"]: p.get("reason", "") for p in result.get("places", [])}
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

    def rerank_places(
        self,
        places: list,
        dog_tags: list | None = None,
        owner_tags: list | None = None,
    ) -> list:
        """Apply profile-based reranking to an existing place candidate list."""
        dog_tags = dog_tags or []
        owner_tags = owner_tags or []

        if not places or not (dog_tags or owner_tags):
            return places

        dog_score_vector = (
            self._dog_scorer.calculate_vector(dog_tags) if dog_tags else {}
        )
        owner_score_vector = (
            self._owner_scorer.calculate_vector(owner_tags) if owner_tags else {}
        )

        logger.info(
            "[PlacesChain] rerank input | dog_tags=%s | owner_tags=%s",
            dog_tags,
            owner_tags,
        )
        logger.info(
            "[PlacesChain] rerank vectors | dog=%s | owner=%s",
            dog_score_vector,
            owner_score_vector,
        )
        logger.info(
            "[PlacesChain] rerank before | top=%s",
            [place.get("name", "") for place in places[:5]],
        )
        return self._rerank(places, dog_score_vector, owner_score_vector)

    def _rerank(
        self,
        places: list,
        dog_score_vector: dict,
        owner_score_vector: dict | None = None,
    ) -> list:
        """Adjust ranking with dog/owner preference vectors."""
        if not places:
            return []

        da = dog_score_vector.get("a", 0)
        db = dog_score_vector.get("b", 0)
        de = dog_score_vector.get("e", 0)

        ov = owner_score_vector or {}
        oa = ov.get("a", 0)
        ob = ov.get("b", 0)
        oc = ov.get("c", 0)
        od = ov.get("d", 0)
        oe = ov.get("e", 0)

        for place in places:
            bonus = 0.0
            category = place.get("category", "")
            sub_category = place.get("sub_category", "")
            category_tokens = {category, sub_category}
            outdoor = place.get("outdoor", "N")
            indoor = place.get("indoor", "N")
            base_score = place.get("final_score", place.get("similarity", 0))

            if de > 3 and outdoor == "Y":
                bonus -= 0.15
            if de > 3 and category_tokens & {"반려견놀이터", "레포츠"}:
                bonus -= 0.15
            if da > 3 and category_tokens & {"공원", "놀이터", "반려견놀이터"}:
                bonus += 0.10
            if db > 3 and category_tokens & {"카페", "관광지", "여행지"}:
                bonus += 0.05

            if oa > 3 and outdoor == "Y":
                bonus += 0.08
            if ob > 3 and category_tokens & {"카페", "관광지", "여행지"}:
                bonus += 0.05
            if oc > 3 and category_tokens & {"공원", "놀이터", "반려견놀이터"}:
                bonus += 0.05
            if od > 3 and (category_tokens & {"카페"} or indoor == "Y"):
                bonus += 0.05
            if oe > 3 and category_tokens & {"카페", "음식점", "식당"}:
                bonus += 0.08

            place["final_score"] = round(base_score + bonus, 4)

        reranked = sorted(places, key=lambda x: x.get("final_score", 0), reverse=True)
        logger.info(
            "[PlacesChain] rerank after | top=%s",
            [place.get("name", "") for place in reranked[:5]],
        )
        return reranked
