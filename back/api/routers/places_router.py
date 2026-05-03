import requests
import os

from core.deps import get_db
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from services.place_service import search_places_from_db
from services.chat_response_service import (
    DispatchContext,
    _load_place_preference_context,
    _rerank_places_with_profile,
    generate_place_reasons,
)

router = APIRouter(tags=["places"])

TOUR_API_KEY = os.getenv("TOUR_API_KEY")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
BASE_URL = "https://apis.data.go.kr/B551011/KorPetTourService2"


def get_place_image(content_id: str) -> str:
    """한국관광공사 detailImage2 API로 장소 이미지 URL 조회.

    searchKeyword2 → detailCommon2 두 단계 호출 방식에서
    content_id 직접 사용으로 변경 (place_service에서 이미 content_id 반환).

    Args:
        content_id: 한국관광공사 콘텐츠 ID (place_service 반환값)

    Returns:
        이미지 URL 문자열. 없으면 빈 문자열.
    """
    if not content_id:
        return ""

    try:
        res = requests.get(
            f"{BASE_URL}/detailImage2",
            params={
                "serviceKey": TOUR_API_KEY,
                "contentId":  content_id,
                "imageYN":    "Y",
                "subImageYN": "Y",
                "MobileOS":   "ETC",
                "MobileApp":  "WithDog",
                "_type":      "json",
            }
        )
        data  = res.json()
        items = data["response"]["body"].get("items")

        if not items or items == "":
            return ""

        item = items["item"]
        item = item[0] if isinstance(item, list) else item
        return item.get("originimgurl", "")

    except Exception as e:
        print(f"관광공사 detailImage2 오류 (content_id={content_id}): {e}")
        return ""


def get_kakao_image(place_name: str) -> str:
    """카카오 이미지 검색 API로 장소 이미지 URL 조회 (fallback).

    관광공사 API에서 이미지를 가져오지 못한 경우에만 호출.
    https 이미지만 허용.

    Args:
        place_name: 장소명

    Returns:
        이미지 URL 문자열. 없으면 빈 문자열.
    """
    if not place_name:
        return ""

    try:
        res = requests.get(
            "https://dapi.kakao.com/v2/search/image",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"},
            params={"query": place_name, "size": 5},
        )
        data = res.json()
        for doc in data.get("documents", []):
            url = doc.get("image_url", "")
            if url.startswith("https://"):
                return url
        return ""

    except Exception as e:
        print(f"카카오 이미지 오류 ({place_name}): {e}")
        return ""


@router.get("/search")
async def search_places(
    query: str,
    request: Request,
    pet_id: int | None = None,
    user_lat: float | None = None,
    user_lng: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    """장소 검색 엔드포인트.

    흐름:
        1. place_service 하이브리드 검색 (RDB 필터 → ChromaDB 유사도)
        2. 각 장소 이미지 보강
            - 1순위: 한국관광공사 detailImage2 (content_id 직접 사용)
            - 2순위: 카카오 이미지 검색 (fallback)

    Args:
        query:   사용자 검색 쿼리 (예: "강남 카페")
        request: FastAPI Request (AIContainer 접근용)
        db:      비동기 DB 세션

    Returns:
        {"places": [...]} 형태의 장소 목록
    """
    places = await search_places_from_db(
        query, db, n_results=5, request=request,
        user_lat=user_lat, user_lng=user_lng,
    )
    profile_ctx = await _load_place_preference_context(
        DispatchContext(db=db, pet_id=pet_id)
    )
    places = _rerank_places_with_profile(places, profile_ctx, request=request)

    for place in places:
        # 1순위: 관광공사 detailImage2 (content_id 직접 사용, API 호출 1회로 단축)
        image = get_place_image(place["content_id"])

        # 2순위: 카카오 이미지 검색 fallback
        if not image:
            image = get_kakao_image(place["name"])

        place["image"] = image

    reasons = await generate_place_reasons(query, places)
    for place in places:
        place["reason"] = reasons.get(place["name"], "")

    return {"places": places}
