# -*- coding: utf-8 -*-
from ai.core.interfaces.base_scorer import BaseScorer

class OwnerScorer(BaseScorer):

    # 보호자 태그 점수표 (기존 OWNER_TAG_SCORES 그대로)
    _TAG_SCORES = {
        "신나게 뛰어놀기":    {"a": 1,  "b": 5,  "c": 0,  "d": 0,  "e": 1},
        "느긋하게 쉬어가기":  {"a": 2,  "b": -2, "c": 0,  "d": 3,  "e": 0},
        "자연 속으로":        {"a": 5,  "b": 1,  "c": -1, "d": 2,  "e": 0},
        "도시 구경":          {"a": -2, "b": 1,  "c": 3,  "d": 1,  "e": 2},
        "일상 충전":          {"a": 1,  "b": -1, "c": 0,  "d": 0,  "e": 1},
        "새로운 곳 구경":     {"a": 0,  "b": 2,  "c": 2,  "d": 1,  "e": 2},
        "감성 충만":          {"a": 1,  "b": -1, "c": 1,  "d": 5,  "e": -1},
        "동네 골목 탐방":     {"a": 1,  "b": 1,  "c": 2,  "d": 2,  "e": 1},
        "계획 없이 떠나기":   {"a": 1,  "b": 2,  "c": 1,  "d": 2,  "e": -1},
        "바다":               {"a": 5,  "b": 2,  "c": 0,  "d": 3,  "e": 0},
        "산":                 {"a": 5,  "b": 4,  "c": 0,  "d": 2,  "e": 0},
        "숲":                 {"a": 5,  "b": 2,  "c": 0,  "d": 3,  "e": 0},
        "계곡":               {"a": 5,  "b": 3,  "c": 0,  "d": 2,  "e": 0},
        "공원 산책":          {"a": 3,  "b": 2,  "c": 2,  "d": 1,  "e": 1},
        "카페 투어":          {"a": -1, "b": 0,  "c": 4,  "d": 3,  "e": 1},
        "핫플 인증":          {"a": -2, "b": 1,  "c": 5,  "d": 4,  "e": 2},
        "사진 건지러":        {"a": 1,  "b": 1,  "c": 2,  "d": 5,  "e": 0},
        "맛있는 거 먹으러":   {"a": -1, "b": 0,  "c": 2,  "d": 1,  "e": 3},
        "전시 관람":          {"a": -1, "b": 1,  "c": 1,  "d": 3,  "e": 1},
    }

    # 보호자 타입 이름표
    _TYPES = {
        "o_a": "🌿 자연 애호가",
        "o_b": "✨ 도시 감성러",
        "o_c": "🏃 활발한 활동가",
        "o_d": "🛋️ 느긋한 휴식러",
    }

    def calculate_vector(self, tags: list[str]) -> dict[str, float]:
        """보호자 태그 → 점수 벡터 반환"""
        scores = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}
        for tag in tags:
            if tag not in self._TAG_SCORES:
                continue
            for axis, value in self._TAG_SCORES[tag].items():
                scores[axis] += value
        return scores

    def classify_type(self, tags: list[str]) -> str:
        """보호자 태그 → 타입 ID 반환"""
        scores = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}
        for tag in tags:
            if tag not in self._TAG_SCORES:
                raise ValueError(f"존재하지 않는 보호자 태그: {tag}")
            for axis, value in self._TAG_SCORES[tag].items():
                scores[axis] += value

        max_score = max(scores.values())

        # 동점 시 o_d 우선
        if scores["d"] == max_score:
            return "o_d"  # 🛋️ 느긋한 휴식러
        elif scores["a"] == max_score:
            return "o_a"  # 🌿 자연 애호가
        elif scores["d"] >= scores["b"] and scores["c"] >= scores["b"]:
            return "o_b"  # ✨ 도시 감성러
        else:
            return "o_c"  # 🏃 활발한 활동가

    def get_type_name(self, type_id: str) -> str:
        """타입 ID → 타입 이름 반환"""
        result = self._TYPES.get(type_id)
        if result is None:
            raise ValueError(f"존재하지 않는 보호자 타입 ID: {type_id}")
        return result