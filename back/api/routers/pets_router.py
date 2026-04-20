# -*- coding: utf-8 -*-
"""
routers/pets.py
---------------
반려견 도메인 HTTP 엔드포인트.

엔드포인트:
    POST   /pets                  반려견 등록 (breed_id FK 검증)
    GET    /pets?user_id={id}     사용자별 목록 (deleted_at IS NULL)
    GET    /pets/{pet_id}         단건 조회
    PATCH  /pets/{pet_id}         정보 수정 (본인만)
    DELETE /pets/{pet_id}         Soft Delete (본인만)

[user_id 처리]
등록 시 user_id는 JWT current_user에서 자동 추출합니다 (요청 바디에서 받지 않음).
목록 조회 시에는 query parameter로 user_id를 받습니다.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from models.user import User
from schemas.pet import PetCreate, PetResponse, PetUpdate
from services import pet_service as pet_svc

router = APIRouter(tags=["Pets"])


@router.post(
    "",
    response_model=PetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="반려견 등록",
    description=(
        "로그인 사용자의 반려견을 등록합니다.\n\n"
        "- `breed_id`: breeds 테이블 참조 검증\n"
        "- `type_id`: keywords 테이블 참조 검증\n"
        "- `user_id`는 JWT에서 자동 추출됩니다."
    ),
)
async def create_pet(
    data: PetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PetResponse:
    pet = await pet_svc.create_pet(data, db, current_user.id)
    return PetResponse.model_validate(pet)


@router.get(
    "",
    response_model=list[PetResponse],
    summary="사용자별 반려견 목록 조회",
)
async def list_pets(
    user_id: Annotated[int, Query(description="조회할 사용자 ID")],
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),  # 인증 필요
) -> list[PetResponse]:
    pets = await pet_svc.list_pets(user_id, db)
    return [PetResponse.model_validate(p) for p in pets]


@router.get(
    "/{pet_id}",
    response_model=PetResponse,
    summary="반려견 단건 조회",
)
async def get_pet(
    pet_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PetResponse:
    pet = await pet_svc.get_pet(pet_id, db)
    return PetResponse.model_validate(pet)


@router.patch(
    "/{pet_id}",
    response_model=PetResponse,
    summary="반려견 정보 수정",
    description=(
        "제공된 필드만 업데이트합니다 (PATCH 시맨틱).\n\n"
        "**본인의 반려견만 수정 가능** (다른 소유자 접근 시 403)"
    ),
)
async def update_pet(
    pet_id: int,
    data: PetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PetResponse:
    pet = await pet_svc.update_pet(pet_id, data, db, current_user.id)
    return PetResponse.model_validate(pet)


@router.delete(
    "/{pet_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="반려견 삭제 (Soft Delete)",
    description="**본인의 반려견만 삭제 가능** (다른 소유자 접근 시 403)",
)
async def delete_pet(
    pet_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await pet_svc.delete_pet(pet_id, db, current_user.id)
