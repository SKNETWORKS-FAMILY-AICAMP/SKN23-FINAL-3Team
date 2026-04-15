# -*- coding: utf-8 -*-
"""
schemas/image.py
----------------
이미지 도메인 Pydantic v2 스키마.

ImageResponse: 이미지 단건 응답 스키마
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageResponse(BaseModel):
    """이미지 단건 응답."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="이미지 ID")
    file_url: str = Field(..., description="AWS S3 파일 URL")
    file_name: str = Field(..., description="원본 파일명")
    created_at: datetime = Field(..., description="생성 일시")
