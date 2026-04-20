# -*- coding: utf-8 -*-
"""
services/pet.py
---------------
반려견 도메인 서비스 레이어 (DB 쿼리 + 비즈니스 로직 통합).

주요 함수:
    - create_pet() : 등록 (breed_id / type_id FK 무결성 검증)
    - list_pets()  : 사용자별 목록 (deleted_at IS NULL)
    - get_pet()    : 단건 조회
    - update_pet() : 정보 수정 (본인 확인 + FK 검증)
    - delete_pet() : Soft Delete (본인 확인)

[소유권 정책]
반려견의 수정 · 삭제는 등록한 사용자(pet.user_id == current_user_id) 본인만 가능합니다.
"""

from __future__ import annotations

from models.pet import Pet
from typing import Sequence
from sqlalchemy import select
from core.utils import kst_now
from models.breed import Breed
from models.keyword import Keyword
from fastapi import HTTPException, status
from schemas.pet import PetCreate, PetUpdate
from sqlalchemy.ext.asyncio import AsyncSession

# ── 내부 헬퍼 ────────────────────────────────────────────────────────────────

def _assert_owner(pet: Pet, current_user_id: int) -> None:
    """요청자가 해당 반려견의 보호자인지 검증합니다."""
    if pet.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="본인의 반려견만 수정/삭제할 수 있습니다.",
        )


async def _verify_breed(breed_id: int, db: AsyncSession) -> None:
    """breed_id FK: 견종이 존재하는지 검증합니다."""

    result = await db.execute(select(Breed).where(Breed.id == breed_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"견종(id={breed_id})을 찾을 수 없습니다.",
        )


async def _verify_keyword(keyword_id: int, db: AsyncSession) -> None:
    """type_id FK: 키워드가 존재하는지 검증합니다."""

    result = await db.execute(select(Keyword).where(Keyword.id == keyword_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"성격 키워드(id={keyword_id})를 찾을 수 없습니다.",
        )


# ── 공개 서비스 함수 ─────────────────────────────────────────────────────────

async def _get_default_keyword_id(db: AsyncSession) -> int:
    """type_id 미전송 시 PET 카테고리 첫 번째 키워드 ID를 반환합니다."""
    from models.keyword import Keyword
    result = await db.execute(
        select(Keyword).where(Keyword.category == "PET").limit(1)
    )
    keyword = result.scalar_one_or_none()
    if keyword is None:
        # PET 카테고리 없으면 전체에서 첫 번째
        result = await db.execute(select(Keyword).limit(1))
        keyword = result.scalar_one_or_none()
    if keyword is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="등록된 키워드가 없습니다. 관리자에게 문의하세요.",
        )
    return keyword.id


async def create_pet(
    data: PetCreate,
    db: AsyncSession,
    current_user_id: int,
) -> Pet:
    """
        반려견을 등록합니다.

        user_id는 current_user_id로 자동 설정됩니다 (요청 바디에서 받지 않음).
        type_id 미전송 시 PET 카테고리 첫 번째 키워드를 자동 사용합니다.

        Args:
                data           : PetCreate 요청 데이터
                db             : AsyncSession
                current_user_id: 현재 로그인 사용자 ID

        Returns:
                생성된 Pet ORM 객체

        Raises:
                HTTPException 404: breed_id 또는 type_id 참조 불일치
    """
    # gender 필수 검증
    if data.gender is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="반려견 성별(gender)은 필수 항목입니다.",
        )

    # FK 무결성 검증
    await _verify_breed(data.breed_id, db)

    # type_id: 미전송 시 첫 번째 PET 키워드 자동 사용
    type_id = data.type_id
    if type_id is None:
        type_id = await _get_default_keyword_id(db)
    else:
        await _verify_keyword(type_id, db)

    pet = Pet(
        user_id=current_user_id,
        breed_id=data.breed_id,
        name=data.name,
        birth_date=data.birth_date,
        gender=data.gender,
        is_neutered=data.is_neutered,
        type_id=type_id,
        selected_tags=data.selected_tags,
    )
    db.add(pet)
    await db.flush()
    await db.refresh(pet)

    return pet


async def list_pets(user_id: int, db: AsyncSession) -> Sequence[Pet]:
    """
        사용자별 반려견 목록 조회 (deleted_at IS NULL, 최신 등록순).

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
        반려견 단건 조회.

        Raises:
                HTTPException 404: 존재하지 않거나 삭제된 반려견
    """
    result = await db.execute(
        select(Pet).where(Pet.id == pet_id, Pet.deleted_at.is_(None))
    )
    pet = result.scalar_one_or_none()

    if pet is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"반려견(id={pet_id})을 찾을 수 없습니다.",
        )

    return pet


async def update_pet(
    pet_id: int,
    data: PetUpdate,
    db: AsyncSession,
    current_user_id: int,
) -> Pet:
    """
        반려견 정보를 수정합니다.

        제공된 필드만 업데이트합니다 (PATCH 시맨틱).
        breed_id / type_id 변경 시 FK 무결성 검증을 수행합니다.

        Raises:
                HTTPException 403: 본인 반려견 아님
                HTTPException 404: 반려견 / 견종 / 키워드 없음
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
        반려견 Soft Delete.

        Raises:
                HTTPException 403: 본인 반려견 아님
                HTTPException 404: 반려견 없음
    """
    pet = await get_pet(pet_id, db)
    _assert_owner(pet, current_user_id)

    pet.deleted_at = kst_now()
    await db.flush()
