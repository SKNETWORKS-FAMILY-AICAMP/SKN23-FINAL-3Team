# -*- coding: utf-8 -*-
"""
services/keyword_service.py
---------------------------
키워드 도메인 서비스 레이어.

주요 함수:
    - list_keywords(): 전체 목록 조회 (category 필터 지원)

keywords 테이블은 마스터 데이터이므로 엔드포인트 레벨 CUD 없음.
데이터 초기 적재는 db/seeds/keywords_seed.py 참조.
"""

from __future__ import annotations

from typing import Sequence
from sqlalchemy import select
from models.keyword import Keyword
from sqlalchemy.ext.asyncio import AsyncSession


async def list_keywords(
    db: AsyncSession,
    *,
    category: str | None = None,
) -> Sequence[Keyword]:
    """
    키워드 목록을 조회합니다.

    Args:
        db      : AsyncSession
        category: "PET" 또는 "USER" — 지정하면 해당 분류만 반환

    Returns:
        Keyword ORM 객체 목록 (id 오름차순)
    """
    stmt = select(Keyword)

    if category is not None:
        stmt = stmt.where(Keyword.category == category.upper())

    stmt = stmt.order_by(Keyword.id.asc())

    result = await db.execute(stmt)
    return result.scalars().all()
