# -*- coding: utf-8 -*-
"""
services/pet.py
---------------
반려동물 도메인 서비스 레이어 (DB 쿼리 + 비즈니스 로직 통합).

주요 함수:
    - create_pet() : 등록 (breed_id / type_id FK 무결성 검증)
    - list_pets()  : 사용자별 목록 (deleted_at IS NULL)
    - get_pet()    : 단건 조회
    - update_pet() : 정보 수정 (본인 확인 + FK 검증)
    - delete_pet() : Soft Delete (본인 확인)

[소유권 정책]
반려동물의 수정 · 삭제는 등록한 사용자(pet.user_id == current_user_id) 본인만 가능합니다.
"""

from __future__ import annotations

from datetime import datetime
from core.utils import kst_now
from typing import Sequence

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.pet import Pet
from schemas.pet import PetCreate, PetUpdate


# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────

def _assert_owner(pet: Pet, current_user_id: int) -> None:
    """요청자가 해당 반려동물의 보호자인지 검증합니다."""
    if pet.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 반려동물만 수정/삭제할 수 있습니다.",
        )


async def _verify_breed(breed_id: int, db: AsyncSession) -> None:
    """breed_id FK: 견종이 존재하는지 검증합니다."""
    from models.breed import Breed

    result = await db.execute(select(Breed).where(Breed.id == breed_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"견종(id={breed_id})을 찾을 수 없습니다.",
        )


async def _verify_keyword(keyword_id: int, db: AsyncSession) -> None:
    """type_id FK: 키워드가 존재하는지 검증합니다."""
    from models.keyword import Keyword

    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"성격 키워드(id={keyword_id})를 찾을 수 없습니다.",
        )


# ── 공개 서비스 함수 ─────────────────────────────────────────────────────────

async def create_pet(
    data: PetCreate,
    db: AsyncSession,
    current_user_id: int,
) -> Pet:
    """
        반려동물을 등록합니다.

        user_id는 current_user_id로 자동 설정됩니다 (요청 바디에서 받지 않음).

        Args:
                data           : PetCreate 요청 데이터
                db             : AsyncSession
                current_user_id: 현재 로그인 사용자 ID

        Returns:
                생성된 Pet ORM 객체

        Raises:
                HTTPException 404: breed_id 또는 type_id 참조 불일치
    """
    # FK 무결성 검증
    await _verify_breed(data.breed_id, db)
    await _verify_keyword(data.type_id, db)

    pet = Pet(
        user_id=current_user_id,
        breed_id=data.breed_id,
        name=data.name,
        birth_date=data.birth_date,
        gender=data.gender,
        is_neutered=data.is_neutered,
        type_id=data.type_id,
        selected_tags=data.selected_tags,
    )
    db.add(pet)
    await db.flush()
    await db.refresh(pet)

    return pet


async def list_pets(user_id: int, db: AsyncSession) -> Sequence[Pet]:
    """
        사용자별 반려동물 목록 조회 (deleted_at IS NULL, 최신 등록순).

        Args:
                user_id: 조회할 사용자 ID
                db     : AsyncSession

        Returns:
                Pet ORM 객체 목록
    """
    result = await db.execute(
        select(Pet)
        .where(Pet.user_id == user_id, Pet.deleted_at.is_(None))
        .order_by(Pet.created_at.desc())
    )
    return result.scalars().all()


async def get_pet(pet_id: int, db: AsyncSession) -> Pet:
    """
        반려동물 단건 조회.

        Raises:
                HTTPException 404: 존재하지 않거나 삭제된 반려동물
    """
    result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.deleted_at.is_(None))
    )
    pet = result.scalar_one_or_none()

    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"반려동물(id={pet_id})을 찾을 수 없습니다.",
        )

    return pet


async def update_pet(
    pet_id: int,
    data: PetUpdate,
    db: AsyncSession,
    current_user_id: int,
) -> Pet:
    """
        반려동물 정보를 수정합니다.

        제공된 필드만 업데이트합니다 (PATCH 시맨틱).
        breed_id / type_id 변경 시 FK 무결성 검증을 수행합니다.

        Raises:
                HTTPException 403: 본인 반려동물 아님
                HTTPException 404: 반려동물 / 견종 / 키워드 없음
    """
    pet = await get_pet(pet_id, db)
    _assert_owner(pet, current_user_id)

    update_data = data.model_dump(exclude_unset=True)

    if not update_data:
        return pet

    # FK 무결성 검증
    if "breed_id" in update_data:
        await _verify_breed(update_data["breed_id"], db)

    if "type_id" in update_data:
        await _verify_keyword(update_data["type_id"], db)

    for field, value in update_data.items():
        setattr(pet, field, value)

    await db.flush()
    await db.refresh(pet)

    return pet


async def delete_pet(
    pet_id: int,
    db: AsyncSession,
    current_user_id: int,
) -> None:
    """
        반려동물 Soft Delete.

        Raises:
                HTTPException 403: 본인 반려동물 아님
                HTTPException 404: 반려동물 없음
    """
    pet = await get_pet(pet_id, db)
    _assert_owner(pet, current_user_id)

    pet.deleted_at = kst_now()
    await db.flush()
