# -*- coding: utf-8 -*-
"""
core/utils.py
-------------
공용 유틸리티 함수 모음.
"""

from datetime import datetime, timezone, timedelta

# KST(UTC+9) timezone 상수
KST = timezone(timedelta(hours=9))


def kst_now() -> datetime:
    """KST(UTC+9) 현재 시각을 timezone-naive datetime으로 반환합니다."""
    return datetime.now(KST).replace(tzinfo=None)
