# -*- coding: utf-8 -*-
"""
utils/validation.py
-------------------
입력 검증 공통 헬퍼.

- clean_text           : trim + 빈 문자열 거부 + 길이 cap. Pydantic field_validator(mode="before") 안에서 사용.
- validate_user_birth  : 사용자 생년월일 범위 (1900-01-01 ~ 오늘-14년, 만 14세 이상).
- validate_pet_birth   : 반려견 생년월일 범위 (오늘-30년 ~ 오늘).

가을쥐 정책 (2026-05-07 외부팀 QA #62·#63 결정) 권위.
도배(연속 동일 문자) 차단 미적용.
"""

from __future__ import annotations

from datetime import date


def clean_text(
    value: str | None,
    *,
    min_length: int,
    max_length: int,
    label: str,
    allow_blank: bool = False,
) -> str | None:
    """문자열 trim + 길이 검증.

    Args:
        value: 원본 입력 (None 허용 — Optional 필드용).
        min_length: trim 후 최소 길이. 0 = blank OK.
        max_length: trim 후 최대 길이.
        label: 에러 메시지에 들어갈 사용자용 필드명 (예: "닉네임").
        allow_blank: True 면 빈 문자열·공백만 통과 (NULL 허용 + 빈 OK 필드용).

    Returns:
        trim 된 문자열, 또는 None (입력이 None 일 때).

    Raises:
        ValueError: 길이 위반·빈 문자열 거부 시 한국어 메시지.
    """
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        if allow_blank or min_length == 0:
            return cleaned
        raise ValueError(f"{label}을(를) 입력해주세요")
    if len(cleaned) < min_length:
        raise ValueError(f"{label}은(는) {min_length}자 이상이어야 합니다")
    if len(cleaned) > max_length:
        raise ValueError(f"{label}은(는) {max_length}자 이하로 입력해주세요")
    return cleaned


def _safe_replace_year(today: date, *, years_offset: int) -> date:
    """today.replace(year=today.year + years_offset). 윤년(2/29) 폴백 포함."""
    target_year = today.year + years_offset
    try:
        return today.replace(year=target_year)
    except ValueError:
        return today.replace(year=target_year, day=28)


def validate_user_birth(value: date | None) -> date | None:
    """사용자 생년월일 범위 검증.

    정책: 1900-01-01 <= value <= (오늘 - 14년).
    개인정보보호법 정렬 — 만 14세 이상만 가입 가능.

    Args:
        value: 검증 대상 (None 허용).

    Returns:
        검증 통과한 date, 또는 None.

    Raises:
        ValueError: 범위 위반 시 한국어 메시지.
    """
    if value is None:
        return None
    today = date.today()
    min_date = date(1900, 1, 1)
    max_date = _safe_replace_year(today, years_offset=-14)
    if value < min_date:
        raise ValueError("생년월일은 1900년 이후로 입력해주세요")
    if value > max_date:
        raise ValueError("만 14세 이상만 가입 가능합니다")
    return value


def validate_pet_birth(value: date | None) -> date | None:
    """반려견 생년월일 범위 검증.

    정책: (오늘 - 30년) <= value <= 오늘.

    Args:
        value: 검증 대상 (None 허용).

    Returns:
        검증 통과한 date, 또는 None.

    Raises:
        ValueError: 범위 위반 시 한국어 메시지.
    """
    if value is None:
        return None
    today = date.today()
    min_date = _safe_replace_year(today, years_offset=-30)
    if value < min_date:
        raise ValueError("반려견 생년월일은 30년 이내로 입력해주세요")
    if value > today:
        raise ValueError("반려견 생년월일은 오늘 이전이어야 합니다")
    return value
