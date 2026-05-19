# -*- coding: utf-8 -*-
"""schemas/* 의 field_validator 단위 테스트.

가을쥐 정책 (#62·#63 — 마이페이지 입력 검증 디폴트, 2026-05-07 결정) 권위.
한국어 에러 메시지 문구가 정책에 맞게 raise 되는지 확인.
"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from schemas.chat_room import ChatRoomCreate, ChatRoomUpdateTitle
from schemas.diary import DiaryCreate, DiaryUpdate
from schemas.pet import PetCreate, PetUpdate
from schemas.user import UserUpdate


# ── User ────────────────────────────────────────────────────────────────────

class TestUserNickname:
    def test_정상_닉네임(self):
        m = UserUpdate(nickname="가을쥐")
        assert m.nickname == "가을쥐"

    def test_trim_적용(self):
        m = UserUpdate(nickname="  가을쥐  ")
        assert m.nickname == "가을쥐"

    def test_공백만_거부(self):
        with pytest.raises(ValidationError) as exc:
            UserUpdate(nickname="   ")
        assert "닉네임" in str(exc.value)

    def test_20자_초과_거부(self):
        with pytest.raises(ValidationError) as exc:
            UserUpdate(nickname="가" * 21)
        assert "20자" in str(exc.value)

    def test_None_허용(self):
        m = UserUpdate()
        assert m.nickname is None


class TestUserBirthDate:
    def test_정상_생년월일(self):
        m = UserUpdate(birth_date=date(2000, 1, 1))
        assert m.birth_date == date(2000, 1, 1)

    def test_1900년_이전_거부(self):
        with pytest.raises(ValidationError) as exc:
            UserUpdate(birth_date=date(1899, 12, 31))
        assert "1900년" in str(exc.value)

    def test_만_14세_미만_거부(self):
        too_young = date.today() - timedelta(days=10)
        with pytest.raises(ValidationError) as exc:
            UserUpdate(birth_date=too_young)
        assert "14세" in str(exc.value)

    def test_None_허용(self):
        m = UserUpdate()
        assert m.birth_date is None


# ── Pet ─────────────────────────────────────────────────────────────────────

class TestPetName:
    def test_정상_이름(self):
        m = PetCreate(breed_id=1, name="메리", gender=None)
        assert m.name == "메리"

    def test_20자_초과_거부(self):
        with pytest.raises(ValidationError) as exc:
            PetCreate(breed_id=1, name="가" * 21)
        assert "20자" in str(exc.value)

    def test_공백만_거부(self):
        with pytest.raises(ValidationError):
            PetCreate(breed_id=1, name="   ")

    def test_update_None_허용(self):
        m = PetUpdate()
        assert m.name is None


class TestPetBirthDate:
    def test_정상_생년월일(self):
        valid = date.today() - timedelta(days=365)
        m = PetCreate(breed_id=1, name="메리", birth_date=valid)
        assert m.birth_date == valid

    def test_30년_이전_거부(self):
        too_old = date.today() - timedelta(days=31 * 365)
        with pytest.raises(ValidationError) as exc:
            PetCreate(breed_id=1, name="메리", birth_date=too_old)
        assert "30년" in str(exc.value)

    def test_미래_날짜_거부(self):
        future = date.today() + timedelta(days=1)
        with pytest.raises(ValidationError) as exc:
            PetCreate(breed_id=1, name="메리", birth_date=future)
        assert "오늘 이전" in str(exc.value)


# ── ChatRoom ────────────────────────────────────────────────────────────────

class TestChatRoomTitle:
    def test_create_None_허용(self):
        m = ChatRoomCreate()
        assert m.title is None

    def test_create_빈_허용(self):
        m = ChatRoomCreate(title="   ")
        assert m.title == ""

    def test_create_50자_초과_거부(self):
        with pytest.raises(ValidationError) as exc:
            ChatRoomCreate(title="가" * 51)
        assert "50자" in str(exc.value)

    def test_update_공백만_거부(self):
        with pytest.raises(ValidationError):
            ChatRoomUpdateTitle(title="   ")

    def test_update_50자_초과_거부(self):
        with pytest.raises(ValidationError) as exc:
            ChatRoomUpdateTitle(title="가" * 51)
        assert "50자" in str(exc.value)

    def test_update_정상(self):
        m = ChatRoomUpdateTitle(title="새 제목")
        assert m.title == "새 제목"


# ── Diary ───────────────────────────────────────────────────────────────────

class TestDiaryFields:
    def test_title_50자_초과_거부(self):
        with pytest.raises(ValidationError) as exc:
            DiaryCreate(pet_id=1, title="가" * 51)
        assert "50자" in str(exc.value)

    def test_title_정상(self):
        m = DiaryCreate(pet_id=1, title="좋은 하루")
        assert m.title == "좋은 하루"

    def test_title_None_허용(self):
        m = DiaryCreate(pet_id=1)
        assert m.title is None

    def test_6W_1000자_초과_거부(self):
        with pytest.raises(ValidationError) as exc:
            DiaryCreate(pet_id=1, when_text="가" * 1001)
        assert "1000자" in str(exc.value)

    def test_6W_None_허용(self):
        m = DiaryCreate(pet_id=1)
        assert m.when_text is None
        assert m.where_text is None
        assert m.who_text is None
        assert m.what_text is None
        assert m.how_text is None
        assert m.why_text is None

    def test_6W_빈_허용(self):
        m = DiaryCreate(pet_id=1, when_text="   ")
        assert m.when_text == ""

    def test_content_공백만_거부(self):
        with pytest.raises(ValidationError):
            DiaryCreate(pet_id=1, content="   ")

    def test_content_정상(self):
        m = DiaryCreate(pet_id=1, content="좋은 하루였다.")
        assert m.content == "좋은 하루였다."

    def test_update_동일_규칙(self):
        with pytest.raises(ValidationError):
            DiaryUpdate(title="가" * 51)
