# -*- coding: utf-8 -*-
"""
schemas/breed.py
----------------
견종 도메인 Pydantic v2 스키마.

BreedResponse: 견종 단건/목록 응답 스키마
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BreedResponse(BaseModel):
    """견종 단건 응답."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="견종 ID")
    name_ko: str = Field(..., description="견종명 (한국어)")
    name_en: str = Field(..., description="견종명 (영어)")
    top10: bool = Field(..., description="인기 TOP10 여부")
    created_at: datetime = Field(..., description="등록 일시")
