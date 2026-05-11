# -*- coding: utf-8 -*-
"""
성향 점수 단위 테스트

실행:
    # 프로젝트 루트에서
    pytest ai/evaluation/test_scorer.py -v
"""
import sys
from pathlib import Path
from unittest.mock import MagicMock

# Django 의존성 없이 PlacesChain import
sys.modules.setdefault("core", MagicMock())
sys.modules.setdefault("core.database", MagicMock())

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ai.scorers.dog_scorer import DogScorer
from ai.scorers.owner_scorer import OwnerScorer
from ai.chains.places_chain import PlacesChain

DOG_TEST_SCORES = {
    "에너자이저": {"a": 5, "b": 2, "c": 0, "d": 2, "e": -1},
    "산책이 제일 좋아": {"a": 4, "b": 0, "c": 1, "d": 3, "e": -1},
    "밖이 좋아요": {"a": 3, "b": 0, "c": 1, "d": 3, "e": -1},
    "사람이라면 다 좋아": {"a": 0, "b": 5, "c": 2, "d": 1, "e": -1},
    "낯선 사람도 좋아요": {"a": 0, "b": 4, "c": 1, "d": 1, "e": -1},
    "강아지 친구 환영": {"a": 2, "b": 4, "c": 1, "d": 1, "e": -1},
    "집이 편해요": {"a": -2, "b": 0, "c": 2, "d": -1, "e": 2},
    "혼자도 잘 놀아요": {"a": -1, "b": -2, "c": 3, "d": 0, "e": -1},
    "호기심 폭발": {"a": 3, "b": 0, "c": -1, "d": 5, "e": -1},
    "제 갈 길 가는 타입": {"a": 1, "b": -2, "c": 2, "d": 2, "e": 0},
    "겁쟁이": {"a": -2, "b": -2, "c": -4, "d": -2, "e": 5},
    "예민한 편": {"a": 0, "b": -2, "c": -3, "d": 0, "e": 5},
}

OWNER_TEST_SCORES = {
    "자연 속으로": {"a": 5, "b": 1, "c": -1, "d": 2, "e": 0},
    "산": {"a": 5, "b": -2, "c": 0, "d": 2, "e": 0},
    "숲": {"a": 5, "b": 2, "c": 0, "d": 3, "e": 0},
    "신나게 뛰어놀기": {"a": 1, "b": 3, "c": 0, "d": 0, "e": 1},
    "도시 구경": {"a": -2, "b": 1, "c": 3, "d": 1, "e": 2},
    "핫플 인증": {"a": -2, "b": 1, "c": 5, "d": -2, "e": 2},
    "느긋하게 쉬어가기": {"a": 2, "b": -2, "c": 0, "d": 3, "e": 0},
    "감성 충만": {"a": 1, "b": -1, "c": 1, "d": 5, "e": -1},
    "맛있는 거 먹으러": {"a": -1, "b": 0, "c": 2, "d": 1, "e": 3},
    "일상 충전": {"a": 1, "b": -1, "c": 0, "d": 0, "e": 1},
}

dog = DogScorer(DOG_TEST_SCORES)
owner = OwnerScorer(OWNER_TEST_SCORES)


# ─────────────────────────────────────────────
# DogScorer: 타입 분류
# ─────────────────────────────────────────────

def test_dog_type_outdoor_active():
    """활동성·야외 태그 → outdoor_active (산책 탐험대)"""
    tags = ["에너자이저", "산책이 제일 좋아", "밖이 좋아요"]
    assert dog.classify_type(tags) == "outdoor_active"


def test_dog_type_social_friendly():
    """사회성·친화 태그 → social_friendly (모두의 단짝)"""
    tags = ["사람이라면 다 좋아", "낯선 사람도 좋아요", "강아지 친구 환영"]
    assert dog.classify_type(tags) == "social_friendly"


def test_dog_type_careful_pup():
    """실내·독립 태그 → careful_pup (조심스러운 아이)"""
    tags = ["집이 편해요", "혼자도 잘 놀아요"]
    assert dog.classify_type(tags) == "careful_pup"


def test_dog_type_free_spirited():
    """호기심·자유 태그 → free_spirited (자유로운 영혼)"""
    tags = ["호기심 폭발", "제 갈 길 가는 타입"]
    assert dog.classify_type(tags) == "free_spirited"


def test_dog_type_highly_sensitive():
    """예민·겁 태그 → highly_sensitive (예민한 감수성)"""
    tags = ["겁쟁이", "예민한 편"]
    assert dog.classify_type(tags) == "highly_sensitive"


# ─────────────────────────────────────────────
# OwnerScorer: 타입 분류
# ─────────────────────────────────────────────

def test_owner_type_nature_lover():
    """자연·산·숲 태그 → nature_lover (자연 애호가)"""
    tags = ["자연 속으로", "산", "숲"]
    assert owner.classify_type(tags) == "nature_lover"


def test_owner_type_city_explorer():
    """도시 탐방 태그 → city_explorer (도시 감성러)"""
    tags = ["신나게 뛰어놀기", "도시 구경"]
    assert owner.classify_type(tags) == "city_explorer"


def test_owner_type_active_lifestyle():
    """핫플·활동 태그 → active_lifestyle (활발한 활동가)"""
    tags = ["핫플 인증"]
    assert owner.classify_type(tags) == "active_lifestyle"


def test_owner_type_relaxed_healer():
    """힐링·감성 태그 → relaxed_healer (느긋한 휴식러)"""
    tags = ["느긋하게 쉬어가기", "감성 충만"]
    assert owner.classify_type(tags) == "relaxed_healer"


def test_owner_type_foodie_explorer():
    """먹거리 태그 → foodie_explorer (맛집 탐방러)"""
    tags = ["맛있는 거 먹으러"]
    assert owner.classify_type(tags) == "foodie_explorer"


# ─────────────────────────────────────────────
# 동점 처리 (TIE_PRIORITY)
# ─────────────────────────────────────────────

def test_owner_tie_d_over_a():
    """owner a=d 동점 → d 우선(relaxed_healer)"""
    tags = ["느긋하게 쉬어가기", "일상 충전"]
    vec  = owner.calculate_vector(tags)
    assert vec["a"] == vec["d"], "전제: a=d 동점이어야 함"
    assert owner.classify_type(tags) == "relaxed_healer"


# ─────────────────────────────────────────────
# 엣지 케이스
# ─────────────────────────────────────────────

def test_empty_tags_returns_zero_vector():
    assert dog.calculate_vector([])   == {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}
    assert owner.calculate_vector([]) == {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}


def test_unknown_tags_are_ignored():
    """모르는 태그는 점수에 영향 없음"""
    vec_known   = dog.calculate_vector(["에너자이저"])
    vec_unknown = dog.calculate_vector(["에너자이저", "존재하지않는태그"])
    assert vec_known == vec_unknown


def test_get_type_name_all_dog():
    for tid in ["outdoor_active", "social_friendly", "careful_pup", "free_spirited", "highly_sensitive"]:
        assert dog.get_type_name(tid)  # 비어있지 않으면 통과


def test_get_type_name_all_owner():
    for tid in ["nature_lover", "city_explorer", "active_lifestyle", "relaxed_healer", "foodie_explorer"]:
        assert owner.get_type_name(tid)


def test_get_type_name_invalid():
    import pytest
    with pytest.raises(ValueError):
        dog.get_type_name("unknown_dog_type")
    with pytest.raises(ValueError):
        owner.get_type_name("unknown_owner_type")


# ─────────────────────────────────────────────
# _rerank: 보정 bonus 검증
# ─────────────────────────────────────────────

def _make_chain() -> PlacesChain:
    """__init__ 없이 _rerank만 테스트"""
    return PlacesChain.__new__(PlacesChain)


def test_rerank_dog_sensitive_penalizes_outdoor():
    """de(자극민감도) > 3 → 야외 장소 -0.10 (0.9-0.10=0.80 < 카페 0.85)"""
    chain = _make_chain()
    places = [
        {"name": "공원", "category": "공원", "outdoor": "Y", "indoor": "N", "similarity": 0.9},
        {"name": "카페", "category": "카페", "outdoor": "N", "indoor": "Y", "similarity": 0.85},
    ]
    result = chain._rerank(places, {"a": 0, "b": 0, "c": 0, "d": 0, "e": 5})
    assert result[0]["name"] == "카페", "예민한 강아지 → 야외 감점으로 카페가 1위"


def test_rerank_dog_active_boosts_park():
    """da(활동성) > 3 → 공원/놀이터 +0.10"""
    chain = _make_chain()
    places = [
        {"name": "공원", "category": "공원", "outdoor": "Y", "indoor": "N", "similarity": 0.75},
        {"name": "카페", "category": "카페", "outdoor": "N", "indoor": "Y", "similarity": 0.8},
    ]
    result = chain._rerank(places, {"a": 5, "b": 0, "c": 0, "d": 0, "e": 0})
    assert result[0]["name"] == "공원", "활발한 강아지 → 공원 가점으로 공원이 1위"


def test_rerank_owner_nature_boosts_outdoor():
    """oa(자연 선호) > 3 → 야외 장소 +0.08"""
    chain = _make_chain()
    places = [
        {"name": "공원", "category": "공원", "outdoor": "Y", "indoor": "N", "similarity": 0.75},
        {"name": "카페", "category": "카페", "outdoor": "N", "indoor": "Y", "similarity": 0.8},
    ]
    result = chain._rerank(places, {}, {"a": 5, "b": 0, "c": 0, "d": 0, "e": 0})
    assert result[0]["name"] == "공원", "자연 선호 보호자 → 야외 가점으로 공원이 1위"


def test_rerank_owner_foodie_boosts_restaurant():
    """oe(맛집 선호) > 3 → 음식점 +0.08"""
    chain = _make_chain()
    places = [
        {"name": "식당", "category": "음식점", "outdoor": "N", "indoor": "Y", "similarity": 0.75},
        {"name": "공원", "category": "공원",   "outdoor": "Y", "indoor": "N", "similarity": 0.8},
    ]
    result = chain._rerank(places, {}, {"a": 0, "b": 0, "c": 0, "d": 0, "e": 5})
    assert result[0]["name"] == "식당", "맛집 선호 보호자 → 음식점 가점으로 식당이 1위"


def test_rerank_empty_places():
    chain = _make_chain()
    assert chain._rerank([], {"a": 5}, {"a": 5}) == []


def test_rerank_no_owner_vector():
    """owner_score_vector 생략해도 동작"""
    chain = _make_chain()
    places = [
        {"name": "A", "category": "공원", "outdoor": "Y", "indoor": "N", "similarity": 0.8},
    ]
    result = chain._rerank(places, {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0})
    assert result[0]["name"] == "A"
