# -*- coding: utf-8 -*-
"""
services/breed.py
-----------------
견종 도메인 서비스 레이어 (DB 쿼리 + 비즈니스 로직 통합).

주요 함수:
    - list_breeds() : 전체 목록 조회 (top10 필터 / 한·영 검색 지원)
    - get_breed()   : 단건 조회

breeds 테이블은 마스터 데이터이므로 엔드포인트 레벨 CUD 없음.
데이터 초기 적재는 db/seeds/breeds_seed.py 참조.
"""

from __future__ import annotations

from typing import Sequence
from models.breed import Breed
from sqlalchemy import or_, select
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession



async def list_breeds(
    db: AsyncSession,
    *,
    top10: bool | None = None,
    search: str | None = None,
) -> Sequence[Breed]:
    """
        견종 목록을 조회합니다.

        Args:
                db    : AsyncSession
                top10 : True이면 인기 TOP10 견종만 반환
                search: 한국어 또는 영어 견종명 부분 일치 검색 (LIKE)

        Returns:
                Breed ORM 객체 목록 (name_ko 가나다순 정렬)
    """
    stmt = select(Breed)

    if top10 is True:
        stmt = stmt.where(Breed.top10.is_(True))

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            or_(
                Breed.name_ko.like(pattern),
                Breed.name_en.ilike(pattern),   # 영어는 대소문자 무시
            )
        )

    stmt = stmt.order_by(Breed.name_ko.asc())

    result = await db.execute(stmt)
    return result.scalars().all()


async def get_breed(breed_id: int, db: AsyncSession) -> Breed:
    """
        견종 단건 조회.

        Args:
                breed_id: 조회할 견종 ID
                db      : AsyncSession

        Returns:
                Breed ORM 객체

        Raises:
                HTTPException 404: 존재하지 않는 견종 ID
    """
    result = await db.execute(select(Breed).where(Breed.id == breed_id))
    breed = result.scalar_one_or_none()

    if breed is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"견종(id={breed_id})을 찾을 수 없습니다.",
        )

    return breed
