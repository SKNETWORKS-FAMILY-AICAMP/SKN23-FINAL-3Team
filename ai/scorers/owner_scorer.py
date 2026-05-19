# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

from ai.core.interfaces.base_scorer import BaseScorer
from ai.scorers.keyword_score_loader import load_keyword_score_map

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class OwnerScorer(BaseScorer):
    _AXIS_TO_TYPE = {
        "a": "nature_lover",
        "b": "city_explorer",
        "c": "active_lifestyle",
        "d": "relaxed_healer",
        "e": "foodie_explorer",
    }

    _TIE_PRIORITY = ["d", "a", "e", "c", "b"]

    _TYPES = {
        "nature_lover": "자연 선호가",
        "city_explorer": "도시 감성가",
        "active_lifestyle": "활동적인 스타일",
        "relaxed_healer": "느긋한 휴식형",
        "foodie_explorer": "맛집 탐험가",
    }

    def __init__(self, tag_scores: dict[str, dict[str, float]] | None = None):
        self._tag_scores = tag_scores or {}

    async def load_from_db(self, db: "AsyncSession") -> None:
        self._tag_scores = await load_keyword_score_map(db, category="USER")

    def calculate_vector(self, tags: list[str]) -> dict[str, float]:
        scores = {"a": 0.0, "b": 0.0, "c": 0.0, "d": 0.0, "e": 0.0}
        for tag in tags:
            tag_score = self._tag_scores.get(tag)
            if tag_score is None:
                continue
            for axis, value in tag_score.items():
                scores[axis] += value
        return scores

    def classify_type(self, tags: list[str]) -> str:
        scores = self.calculate_vector(tags)
        max_score = max(scores.values())
        for axis in self._TIE_PRIORITY:
            if scores[axis] == max_score:
                return self._AXIS_TO_TYPE[axis]
        raise ValueError("Unable to classify owner type from provided tags")

    def get_type_name(self, type_id: str) -> str:
        result = self._TYPES.get(type_id)
        if result is None:
            raise ValueError(f"존재하지 않는 보호자 타입 ID: {type_id}")
        return result
