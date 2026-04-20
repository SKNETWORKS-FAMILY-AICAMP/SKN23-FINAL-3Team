# -*- coding: utf-8 -*-
"""
routers/diaries.py
------------------
다이어리 도메인 HTTP 엔드포인트.

엔드포인트:
    POST   /diaries                         다이어리 생성 (image_id 없이 1차 저장 가능)
    GET    /diaries?user_id={id}            사용자별 목록 (created_at DESC)
    GET    /diaries?user_id={id}&pet_id={id} 반려동물별 추가 필터
    GET    /diaries/{diary_id}              단건 조회
    PATCH  /diaries/{diary_id}              수정 (image_id 바인딩 포함, 본인만)
    DELETE /diaries/{diary_id}              Soft Delete (본인만)

[2-phase 저장 흐름]
1. POST /diaries        → image_id 없이 생성 (AI 파이프라인 병렬 시작)
2. PATCH /diaries/{id}  → AI 이미지 완성 후 {"image_id": 123} 으로 바인딩
"""

from __future__ import annotations

from typing import Annotated
from models.user import User
from core.deps import get_current_user, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from services import diary_service as diary_svc
from fastapi import APIRouter, Depends, Query, status
from schemas.diary import DiaryCreate, DiaryResponse, DiaryUpdate

router = APIRouter(tags=["Diaries"])


@router.post(
    "",
    response_model=DiaryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="다이어리 생성",
    description=(
        "6하원칙 텍스트를 저장합니다. 모든 텍스트 필드는 optional입니다.\n\n"
        "**2-phase 저장**: `image_id` 없이 먼저 생성하고, "
        "AI 이미지 완성 후 `PATCH`로 `image_id`를 바인딩합니다."
    ),
)
async def create_diary(
    data: DiaryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DiaryResponse:
    diary = await diary_svc.create_diary(data, db, current_user.id)
    return DiaryResponse.model_validate(diary)


@router.get(
    "",
    response_model=list[DiaryResponse],
    summary="다이어리 목록 조회",
    description=(
        "- `user_id`: 사용자별 필터 (필수)\n"
        "- `pet_id`: 반려동물별 추가 필터 (선택)\n"
        "- 정렬: `created_at DESC`"
    ),
)
async def list_diaries(
    user_id: Annotated[int, Query(description="조회할 사용자 ID")],
    pet_id: Annotated[int | None, Query(description="반려동물 ID 필터")] = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DiaryResponse]:
    diaries = await diary_svc.list_diaries(db, user_id=user_id, pet_id=pet_id)
    return [DiaryResponse.model_validate(d) for d in diaries]


@router.get(
    "/{diary_id}",
    response_model=DiaryResponse,
    summary="다이어리 단건 조회",
)
async def get_diary(
    diary_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> DiaryResponse:
    diary = await diary_svc.get_diary(diary_id, db)
    return DiaryResponse.model_validate(diary)


@router.patch(
    "/{diary_id}",
    response_model=DiaryResponse,
    summary="다이어리 수정",
    description=(
        "제공된 필드만 업데이트합니다 (PATCH 시맨틱).\n\n"
        "**image_id 바인딩**: AI 이미지 완성 후 `{\"image_id\": 123}` 형태로 호출하세요.\n\n"
        "**본인 다이어리만 수정 가능** (다른 작성자 접근 시 403)"
    ),
)
async def update_diary(
    diary_id: int,
    data: DiaryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DiaryResponse:
    diary = await diary_svc.update_diary(diary_id, data, db, current_user.id)
    return DiaryResponse.model_validate(diary)


@router.delete(
    "/{diary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="다이어리 삭제 (Soft Delete)",
    description="**본인 다이어리만 삭제 가능** (다른 작성자 접근 시 403)",
)
async def delete_diary(
    diary_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await diary_svc.delete_diary(diary_id, db, current_user.id)
