# -*- coding: utf-8 -*-
"""utils/profanity_filter.py 단위 테스트.

monkeypatch 로 _load_pipeline 을 mock 하여 실제 HuggingFace 모델 다운로드 없이 테스트.
fail-open 동작 (모델 호출 실패 시 False) 확인.

가을쥐 정책 (#71 — 욕설 필터 신규, 2026-05-07 결정) 권위.
"""

from __future__ import annotations

import pytest

from utils import profanity_filter


@pytest.fixture
def mock_pipeline(monkeypatch):
    """_load_pipeline 을 욕설 라벨 mock 으로 교체.

    실제 transformers pipeline 을 안 쓰고 키워드 매칭으로 라벨 score 위조.
    """

    def fake_pipe(text):
        # 욕설 키워드 포함 시 '악플/욕설' 라벨 score 0.95
        if any(bad in text for bad in ("씨발", "병신", "개새끼")):
            return [[
                {"label": "악플/욕설", "score": 0.95},
                {"label": "clean", "score": 0.05},
            ]]
        return [[
            {"label": "clean", "score": 0.99},
            {"label": "악플/욕설", "score": 0.01},
        ]]

    monkeypatch.setattr(profanity_filter, "_load_pipeline", lambda: fake_pipe)
    return fake_pipe


class TestContainsProfanity:
    def test_빈_문자열_False(self):
        assert profanity_filter.contains_profanity("") is False

    def test_None_False(self):
        assert profanity_filter.contains_profanity(None) is False

    def test_공백만_False(self):
        assert profanity_filter.contains_profanity("   ") is False

    def test_욕설_True(self, mock_pipeline):
        assert profanity_filter.contains_profanity("이 씨발놈아") is True

    def test_정상_한국어_False(self, mock_pipeline):
        assert profanity_filter.contains_profanity("안녕하세요 메리예요") is False

    def test_영문_False(self, mock_pipeline):
        assert profanity_filter.contains_profanity("Hello world") is False

    def test_이모지만_False(self, mock_pipeline):
        assert profanity_filter.contains_profanity("🐶🦴") is False


class TestFailOpen:
    """모델 호출 실패 시 False 반환 (보수적 fail-open) 검증.

    검열 누락이 정상 입력 차단보다 운영상 안전 — 모델 다운 시 통과시킴.
    """

    def test_pipeline_예외_False(self, monkeypatch):
        def raise_pipe(text):
            raise RuntimeError("모델 로드 실패")

        monkeypatch.setattr(profanity_filter, "_load_pipeline", lambda: raise_pipe)
        assert profanity_filter.contains_profanity("test text") is False

    def test_load_예외_False(self, monkeypatch):
        def raise_load():
            raise OSError("네트워크 단절")

        monkeypatch.setattr(profanity_filter, "_load_pipeline", raise_load)
        assert profanity_filter.contains_profanity("test text") is False
