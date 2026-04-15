# -*- coding: utf-8 -*-
"""
routers/images.py
-----------------
이미지 도메인 HTTP 엔드포인트.

엔드포인트:
    POST   /images              multipart/form-data 파일 업로드 → S3 + DB 저장
    GET    /images/{image_id}   이미지 단건 조회
    DELETE /images/{image_id}   FK 참조 확인 후 Soft Delete
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.deps import get_current_user, get_db
from schemas.image import ImageResponse
from services import image_service as image_svc

router = APIRouter(tags=["Images"])


@router.post(
    "",
    response_model=ImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="이미지 업로드",
    description="multipart/form-data로 파일을 수신하여 S3에 업로드하고 메타데이터를 DB에 저장합니다.",
)
async def upload_image(
    file: UploadFile = File(..., description="업로드할 이미지 파일"),
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),  # 인증 필수
) -> ImageResponse:
    image = await image_svc.create_image(file, db)
    return ImageResponse.model_validate(image)


@router.get(
    "/{image_id}",
    response_model=ImageResponse,
    summary="이미지 단건 조회",
)
async def get_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
) -> ImageResponse:
    image = await image_svc.get_image(image_id, db)
    return ImageResponse.model_validate(image)


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="이미지 삭제 (Soft Delete)",
    description=(
        "users.profile_id 또는 diaries.image_id에서 참조 중인 경우 "
        "409 Conflict를 반환합니다."
    ),
)
async def delete_image(
    image_id: int,
    db: AsyncSession = Depends(get_db),
    _current_user=Depends(get_current_user),  # 인증 필수
) -> None:
    await image_svc.delete_image(image_id, db)
