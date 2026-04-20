# -*- coding: utf-8 -*-
from ai.core.interfaces.base_scorer import BaseScorer

class DogScorer(BaseScorer):

    # 반려견 태그 점수표 (기존 DOG_TAG_SCORES 그대로)
    _TAG_SCORES = {
        "에너자이저":           {"a": 5,  "b": 2,  "c": 0,  "d": 2,  "e": -1},
        "느긋한 편":            {"a": 1,  "b": 0,  "c": 2,  "d": 0,  "e": 1},
        "애교쟁이":             {"a": 2,  "b": 3,  "c": 1,  "d": 0,  "e": 0},
        "제 갈 길 가는 타입":   {"a": 1,  "b": -2, "c": 2,  "d": 2,  "e": 0},
        "낯을 가려요":          {"a": -1, "b": -3, "c": -2, "d": 0,  "e": 3},
        "낯선 사람도 좋아요":   {"a": 0,  "b": 4,  "c": 1,  "d": 1,  "e": -1},
        "사람이라면 다 좋아":   {"a": 0,  "b": 5,  "c": 2,  "d": 1,  "e": -1},
        "사람은 좀 무서워요":   {"a": 0,  "b": -4, "c": -1, "d": 0,  "e": 2},
        "겁쟁이":               {"a": -2, "b": -2, "c": -4, "d": -2, "e": 5},
        "겁 없는 탐험가":       {"a": 3,  "b": 1,  "c": 3,  "d": 2,  "e": -2},
        "호기심 폭발":          {"a": 3,  "b": 0,  "c": -1, "d": 5,  "e": -1},
        "고집 있는 편":         {"a": 1,  "b": -1, "c": 0,  "d": 2,  "e": 1},
        "예민한 편":            {"a": 0,  "b": -2, "c": -3, "d": 0,  "e": 5},
        "먹는 게 최고":         {"a": 1,  "b": 1,  "c": 1,  "d": 1,  "e": 0},
        "낯선 것엔 짖어요":     {"a": 1,  "b": -1, "c": -2, "d": 0,  "e": 3},
        "산책이 제일 좋아":     {"a": 4,  "b": 0,  "c": 1,  "d": 3,  "e": -1},
        "밖이 좋아요":          {"a": 3,  "b": 0,  "c": 1,  "d": 3,  "e": -1},
        "집이 편해요":          {"a": -2, "b": 0,  "c": 2,  "d": -1, "e": 2},
        "장난감 수집가":        {"a": 3,  "b": 0,  "c": 1,  "d": 2,  "e": 0},
        "공이라면 뭐든지":      {"a": 4,  "b": 1,  "c": 0,  "d": 1,  "e": -1},
        "강아지 친구 환영":     {"a": 2,  "b": 4,  "c": 1,  "d": 1,  "e": -1},
        "혼자도 잘 놀아요":     {"a": -1, "b": -2, "c": 3,  "d": 0,  "e": -1},
        "안기는 거 좋아요":     {"a": 0,  "b": 3,  "c": 3,  "d": 0,  "e": -1},
        "시키는 건 다 해요":    {"a": 1,  "b": 2,  "c": 2,  "d": 1,  "e": -1},
    }

    # 반려견 타입 이름표
    _TYPES = {
        "d_a": "🐾 산책 탐험대",
        "d_b": "🌼 모두의 단짝",
        "d_c": "🌙 조심스러운 아이",
        "d_d": "🍂 자유로운 영혼",
    }

    def calculate_vector(self, tags: list[str]) -> dict[str, float]:
        """반려견 태그 → 점수 벡터 반환"""
        scores = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}
        for tag in tags:
            if tag not in self._TAG_SCORES:
                continue
            for axis, value in self._TAG_SCORES[tag].items():
                scores[axis] += value
        return scores

    def classify_type(self, tags: list[str]) -> str:
        """반려견 태그 → 타입 ID 반환"""
        scores = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}
        for tag in tags:
            if tag not in self._TAG_SCORES:
                raise ValueError(f"존재하지 않는 반려견 태그: {tag}")
            for axis, value in self._TAG_SCORES[tag].items():
                scores[axis] += value

        max_score = max(scores.values())

        # 동점 시 d_c 우선
        if scores["e"] == max_score:
            return "d_c"  # 🌙 조심스러운 아이
        elif scores["a"] >= scores["b"] and scores["d"] >= scores["b"]:
            return "d_a"  # 🐾 산책 탐험대
        elif scores["b"] == max_score:
            return "d_b"  # 🌼 모두의 단짝
        else:
            return "d_d"  # 🍂 자유로운 영혼

    def get_type_name(self, type_id: str) -> str:
        """타입 ID → 타입 이름 반환"""
        result = self._TYPES.get(type_id)
        if result is None:
            raise ValueError(f"존재하지 않는 반려견 타입 ID: {type_id}")
        return result