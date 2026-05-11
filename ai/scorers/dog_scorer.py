# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

from ai.core.interfaces.base_scorer import BaseScorer
from ai.scorers.keyword_score_loader import load_keyword_score_map

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class DogScorer(BaseScorer):
    _AXIS_TO_TYPE = {
        "a": "outdoor_active",
        "b": "social_friendly",
        "c": "careful_pup",
        "d": "free_spirited",
        "e": "highly_sensitive",
    }

    _TIE_PRIORITY = ["e", "a", "b", "d", "c"]

    _TYPES = {
        "outdoor_active": "활동적인 탐험가",
        "social_friendly": "모두의 친구",
        "careful_pup": "조심스러운 아이",
        "free_spirited": "자유로운 영혼",
        "highly_sensitive": "섬세한 감수성",
    }

    def __init__(self, tag_scores: dict[str, dict[str, float]] | None = None):
        self._tag_scores = tag_scores or {}

    async def load_from_db(self, db: "AsyncSession") -> None:
        self._tag_scores = await load_keyword_score_map(db, category="PET")

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
        raise ValueError("Unable to classify dog type from provided tags")

    def get_type_name(self, type_id: str) -> str:
        result = self._TYPES.get(type_id)
        if result is None:
            raise ValueError(f"존재하지 않는 반려견 타입 ID: {type_id}")
        return result
