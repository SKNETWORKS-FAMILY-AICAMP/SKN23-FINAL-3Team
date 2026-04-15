# -*- coding: utf-8 -*-
"""
services/common_service.py
--------------------------
여러 도메인에서 공통으로 사용되는 유틸리티 및 서비스 로직 모듈입니다.
"""

from __future__ import annotations

from datetime import date, datetime

from core.utils import kst_now


def calculate_age(birth_date: date | datetime | str | None, is_traditional: bool = False) -> int | None:
    """
    생년월일을 바탕으로 조회 시점(KST 기준)의 나이를 계산합니다.
    user.birth_date 와 pet.birth_date 등에서 공용으로 사용할 수 있습니다.

    Args:
        birth_date    : 생년월일 (datetime.date, datetime.datetime, 또는 "YYYY-MM-DD" 문자열 지원)
        is_traditional: True인 경우 한국 고유의 '세는 나이'(현재 연도 - 출생 연도 + 1)를 반환.
                        False인 경우 2023년 시행 규칙에 기반한 '만 나이'를 반환 (기본값).
    
    Returns:
        계산된 나이(정수). 생년월일이 없거나 파싱 불가능한 경우 None 반환.
    """
    if not birth_date:
        return None

    # 문자열로 들어오는 경우를 위한 파싱
    if isinstance(birth_date, str):
        try:
            # 타임스탬프 등 복잡한 문자열일 경우 앞 10자리(YYYY-MM-DD)만 파싱
            birth_date = datetime.strptime(birth_date[:10], "%Y-%m-%d").date()
        except ValueError:
            return None

    # datetime인 경우 date로 변환
    if isinstance(birth_date, datetime):
        birth_date = birth_date.date()
        
    # 만약에라도 date 타입이 아니면 방어
    if not isinstance(birth_date, date):
        return None

    # KST 기준 현재 날짜
    current_date = kst_now().date()
    
    if is_traditional:
        # 한국 전통 세는 나이
        return current_date.year - birth_date.year + 1
    
    # 만 나이 (현지 법정 표준)
    age = current_date.year - birth_date.year
    # 올해 생일이 아직 지나지 않았다면 -1
    if (current_date.month, current_date.day) < (birth_date.month, birth_date.day):
        age -= 1
        
    return max(0, age)
