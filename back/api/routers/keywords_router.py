# -*- coding: utf-8 -*-
"""
routers/keywords_router.py
--------------------------
키워드 도메인 HTTP 엔드포인트.

엔드포인트:
    GET /keywords              전체 목록 조회
    GET /keywords?category=PET  반려견 성격 태그만 반환
    GET /keywords?category=USER 사용자 성향 태그만 반환
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db
from schemas.keyword import KeywordResponse
from services import keyword_service as keyword_svc

router = APIRouter(tags=["Keywords"])


@router.get(
    "",
    response_model=list[KeywordResponse],
    summary="키워드 목록 조회",
    description=(
        "온보딩 페이지에서 사용할 태그 목록을 반환합니다.\n\n"
        "- `category=PET` : 반려견 성격 태그\n"
        "- `category=USER`: 사용자 성향 태그\n"
        "- 파라미터 없음 : 전체 반환"
    ),
)
async def list_keywords(
    category: Annotated[
        Literal["PET", "USER"] | None,
        Query(description="분류 필터 (PET / USER)"),
    ] = None,
    db: AsyncSession = Depends(get_db),
) -> list[KeywordResponse]:
    keywords = await keyword_svc.list_keywords(db, category=category)
    return [KeywordResponse.model_validate(k) for k in keywords]
