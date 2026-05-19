# -*- coding: utf-8 -*-
"""
routers/directions_router.py
-----------------------------
카카오모빌리티 길찾기 API 프록시 — 앱에서 Polyline 경로를 표시하기 위해
백엔드가 REST API 키를 이용해 경로 좌표를 가져온다.
"""

from __future__ import annotations

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Request / Response 스키마 ───────────────────────────────────────────────

class DirectionsRequest(BaseModel):
    origin_lat: float = Field(..., description="출발지 위도")
    origin_lng: float = Field(..., description="출발지 경도")
    dest_lat: float = Field(..., description="목적지 위도")
    dest_lng: float = Field(..., description="목적지 경도")
    dest_name: Optional[str] = Field(default=None, description="목적지 이름")


class RoutePoint(BaseModel):
    lat: float
    lng: float


class DirectionsResponse(BaseModel):
    distance: int = Field(..., description="총 거리 (m)")
    duration: int = Field(..., description="총 소요 시간 (s)")
    points: list[RoutePoint] = Field(..., description="경로 좌표 배열")


# ── 엔드포인트 ──────────────────────────────────────────────────────────────

KAKAO_DIRECTIONS_URL = "https://apis-navi.kakaomobility.com/v1/directions"


@router.post("/route", response_model=DirectionsResponse, summary="경로 조회 (Kakao Mobility)")
async def get_route(req: DirectionsRequest) -> DirectionsResponse:
    """
    카카오모빌리티 길찾기 API를 호출하여 출발지→목적지 자동차 경로를 반환한다.

    - 카카오 좌표 순서: **lng, lat** (경도, 위도)
    - sections → roads → vertexes 에서 좌표 추출
    """
    api_key = settings.KAKAO_REST_API_KEY
    if not api_key:
        raise HTTPException(status_code=503, detail="KAKAO_REST_API_KEY가 설정되지 않았습니다.")

    params = {
        "origin": f"{req.origin_lng},{req.origin_lat}",
        "destination": f"{req.dest_lng},{req.dest_lat}",
        "summary": "false",
    }
    headers = {
        "Authorization": f"KakaoAK {api_key}",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(KAKAO_DIRECTIONS_URL, params=params, headers=headers)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="카카오 길찾기 API 응답 시간 초과")
    except httpx.HTTPError as e:
        logger.error(f"[Directions] httpx error: {e}")
        raise HTTPException(status_code=502, detail="카카오 길찾기 API 호출 실패")

    if resp.status_code != 200:
        logger.warning(f"[Directions] Kakao API {resp.status_code}: {resp.text[:300]}")
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"카카오 길찾기 API 오류: {resp.status_code}",
        )

    data = resp.json()

    # 경로가 없는 경우
    routes = data.get("routes", [])
    if not routes:
        raise HTTPException(status_code=404, detail="경로를 찾을 수 없습니다.")

    route = routes[0]
    result_code = route.get("result_code", 0)
    if result_code != 0:
        raise HTTPException(status_code=404, detail="경로를 찾을 수 없습니다.")

    summary = route.get("summary", {})
    distance = summary.get("distance", 0)  # m
    duration = summary.get("duration", 0)  # s

    # sections → roads → vertexes 파싱
    points: list[RoutePoint] = []
    for section in route.get("sections", []):
        for road in section.get("roads", []):
            vertexes = road.get("vertexes", [])
            # vertexes = [lng, lat, lng, lat, ...]
            for i in range(0, len(vertexes) - 1, 2):
                lng = vertexes[i]
                lat = vertexes[i + 1]
                # 중복 제거 (연속 도로 끝/시작점)
                if points and points[-1].lat == lat and points[-1].lng == lng:
                    continue
                points.append(RoutePoint(lat=lat, lng=lng))

    return DirectionsResponse(distance=distance, duration=duration, points=points)
