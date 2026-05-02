from core.deps import get_db
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from services.place_service import search_places_from_db
from services.place_image_service import enrich_place_images
from services.chat_response_service import (
    DispatchContext,
    _load_place_preference_context,
    _rerank_places_with_profile,
    generate_place_reasons,
)

router = APIRouter(tags=["places"])

@router.get("/search")
async def search_places(
    query: str,
    request: Request,
    pet_id: int | None = None,
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
    places = await search_places_from_db(query, db, n_results=5, request=request)
    profile_ctx = await _load_place_preference_context(
        DispatchContext(db=db, pet_id=pet_id)
    )
    places = _rerank_places_with_profile(places, profile_ctx, request=request)

    places = await enrich_place_images(places)

    reasons = await generate_place_reasons(query, places)
    for place in places:
        place["reason"] = reasons.get(place["name"], "")

    return {"places": places}
