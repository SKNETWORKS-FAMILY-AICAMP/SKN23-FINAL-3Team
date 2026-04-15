# -*- coding: utf-8 -*-
"""
schemas/keyword.py
------------------
키워드 도메인 Pydantic v2 스키마.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class KeywordResponse(BaseModel):
    """키워드 단건 응답."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="키워드 ID")
    category: str = Field(..., description="분류 (PET / USER)")
    name: str = Field(..., description="태그명")
    description: str | None = Field(None, description="점수 벡터 (JSON 문자열)")
