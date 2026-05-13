# -*- coding: utf-8 -*-
"""chat_response_service fallback 경로 품질 개선 단위 테스트.

작업 1~3 (프롬프트 리라이팅 · 컨텍스트 주입 · 히스토리 주입) 검증.
OpenAI API 호출은 AsyncMock 으로 모킹합니다.

NOTE: chat_response_service 는 import 체인이 깊어(aioboto3, transformers 등)
직접 import 하면 collect 단계에서 ModuleNotFoundError 가 발생할 수 있습니다.
따라서 모든 import 는 테스트 함수 내부에서 수행합니다.
"""

from __future__ import annotations

from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _import_service():
    """chat_response_service 를 런타임에 import (collect 단계 에러 방지)."""
    import services.chat_response_service as svc
    return svc


# ── 작업 1: 시스템 프롬프트 검증 ──────────────────────────────────────────────

class TestFallbackSystemPrompt:
    @pytest.fixture(autouse=True)
    def _load(self):
        self.svc = _import_service()

    def test_prompt_has_persona(self):
        assert "withDOG" in self.svc._FALLBACK_SYSTEM_PROMPT_TEMPLATE

    def test_prompt_has_tone_rules(self):
        assert "존댓말" in self.svc._FALLBACK_SYSTEM_PROMPT_TEMPLATE
        assert "이모지" in self.svc._FALLBACK_SYSTEM_PROMPT_TEMPLATE

    def test_prompt_has_prohibitions(self):
        assert "수의사" in self.svc._FALLBACK_SYSTEM_PROMPT_TEMPLATE
        assert "추측" in self.svc._FALLBACK_SYSTEM_PROMPT_TEMPLATE

    def test_prompt_has_context_slot(self):
        assert "{pet_context}" in self.svc._FALLBACK_SYSTEM_PROMPT_TEMPLATE

    def test_prompt_has_few_shot_examples(self):
        assert "사용자:" in self.svc._FALLBACK_SYSTEM_PROMPT_TEMPLATE
        assert "assistant:" in self.svc._FALLBACK_SYSTEM_PROMPT_TEMPLATE


# ── 작업 2: 컨텍스트 주입 검증 ────────────────────────────────────────────────

def _make_fake_pet(name="뽀삐", birth_date=date(2024, 3, 1), tags=None):
    return SimpleNamespace(
        name=name,
        birth_date=birth_date,
        selected_tags=tags or ["활발한", "사람을 좋아하는"],
        breed=SimpleNamespace(name_ko="말티즈", name_en="Maltese"),
        deleted_at=None,
    )


def _make_fake_user(nickname="둘리"):
    return SimpleNamespace(nickname=nickname, deleted_at=None)


def _make_fake_db(pet=None, user=None):
    """AsyncSession 모킹 — execute 호출마다 pet → user 순서로 반환."""
    call_count = {"n": 0}

    async def fake_execute(query):
        result = MagicMock()
        call_count["n"] += 1
        if call_count["n"] == 1:
            result.scalar_one_or_none.return_value = pet
        else:
            result.scalar_one_or_none.return_value = user
        return result

    db = AsyncMock()
    db.execute = fake_execute
    return db


@pytest.mark.asyncio
async def test_load_context_with_pet():
    svc = _import_service()
    pet = _make_fake_pet()
    user = _make_fake_user()
    db = _make_fake_db(pet=pet, user=user)
    ctx = svc.DispatchContext(user_id=1, db=db, pet_id=10)

    result = await svc._load_fallback_pet_context(ctx)

    assert "뽀삐" in result
    assert "말티즈" in result
    assert "둘리" in result
    assert "활발한" in result


@pytest.mark.asyncio
async def test_load_context_without_db():
    svc = _import_service()
    ctx = svc.DispatchContext(user_id=1, db=None)
    result = await svc._load_fallback_pet_context(ctx)
    assert result == svc._FALLBACK_NO_PET_CONTEXT


@pytest.mark.asyncio
async def test_load_context_no_pet_found():
    svc = _import_service()
    db = _make_fake_db(pet=None, user=None)
    ctx = svc.DispatchContext(user_id=1, db=db, pet_id=99)
    result = await svc._load_fallback_pet_context(ctx)
    assert result == svc._FALLBACK_NO_PET_CONTEXT


# ── 작업 3: 히스토리 주입 검증 ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chat_completion_with_history():
    """history 전달 시 messages 배열에 히스토리가 포함되는지 검증."""
    svc = _import_service()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="테스트 응답"))]

    with patch.object(svc, "_get_openai_client") as mock_get:
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get.return_value = client

        history = [
            {"role": "user", "content": "안녕"},
            {"role": "assistant", "content": "안녕하세요!"},
        ]
        result = await svc._chat_completion("시스템", "질문", history=history)

        assert result == "테스트 응답"
        call_args = client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        # system + 2 history + user = 4
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "안녕"
        assert messages[2]["content"] == "안녕하세요!"
        assert messages[3]["content"] == "질문"


@pytest.mark.asyncio
async def test_chat_completion_without_history():
    """history=None 시 기존 동작(system + user) 유지."""
    svc = _import_service()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="응답"))]

    with patch.object(svc, "_get_openai_client") as mock_get:
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get.return_value = client

        await svc._chat_completion("시스템", "질문")

        call_args = client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"


@pytest.mark.asyncio
async def test_handle_fallback_injects_pet_context():
    """_handle_fallback 호출 시 프롬프트에 반려견 정보가 주입되는지 검증."""
    svc = _import_service()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="테스트"))]

    pet = _make_fake_pet()
    user = _make_fake_user()
    db = _make_fake_db(pet=pet, user=user)
    ctx = svc.DispatchContext(user_id=1, db=db, pet_id=10)

    with patch.object(svc, "_get_openai_client") as mock_get:
        client = AsyncMock()
        client.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_get.return_value = client

        await svc._handle_fallback("강아지 밥 뭐줘?", ctx=ctx)

        call_args = client.chat.completions.create.call_args
        system_msg = call_args.kwargs["messages"][0]["content"]
        assert "뽀삐" in system_msg
        assert "말티즈" in system_msg
