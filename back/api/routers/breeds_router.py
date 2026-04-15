# -*- coding: utf-8 -*-
"""
routers/breeds.py
-----------------
견종 도메인 HTTP 엔드포인트.

엔드포인트:
    GET /breeds                      전체 목록 조회 (가나다순)
    GET /breeds?top10=true           인기 TOP10만 반환
    GET /breeds?search={keyword}     한/영 견종명 부분 일치 검색
    GET /breeds/{breed_id}           단건 조회
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_db
from schemas.breed import BreedResponse
from services import breed_service as breed_svc

router = APIRouter(tags=["Breeds"])


@router.get(
    "",
    response_model=list[BreedResponse],
    summary="견종 목록 조회",
    description=(
        "- `top10=true`: 인기 TOP10 견종만 반환\n"
        "- `search={keyword}`: 한국어/영어 이름 부분 일치 검색\n"
        "- 두 파라미터 동시 사용 가능 (AND 조건)"
    ),
)
async def list_breeds(
    top10: Annotated[bool | None, Query(description="True이면 인기 TOP10만 반환")] = None,
    search: Annotated[str | None, Query(description="한/영 견종명 부분 검색")] = None,
    db: AsyncSession = Depends(get_db),
) -> list[BreedResponse]:
    breeds = await breed_svc.list_breeds(db, top10=top10, search=search)
    return [BreedResponse.model_validate(b) for b in breeds]


@router.get(
    "/{breed_id}",
    response_model=BreedResponse,
    summary="견종 단건 조회",
)
async def get_breed(
    breed_id: int,
    db: AsyncSession = Depends(get_db),
) -> BreedResponse:
    breed = await breed_svc.get_breed(breed_id, db)
    return BreedResponse.model_validate(breed)
