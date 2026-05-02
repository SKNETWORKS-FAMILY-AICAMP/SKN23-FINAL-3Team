from typing import Annotated
from core.deps import get_db
from schemas.chat_message import FacilityCard
from sqlalchemy.ext.asyncio import AsyncSession
from services.place_image_service import enrich_place_images
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from services.place_service import (lookup_facility_by_name, search_places_from_db)
from services.chat_response_service import (DispatchContext, _load_place_preference_context, _rerank_places_with_profile, generate_place_reasons)

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


@router.get(
    "/by-name",
    response_model=FacilityCard,
    summary="시설정보 단건 조회 (장소명)",
    description=(
        "장소명(`name`)으로 단일 시설의 상세 정보를 반환한다.\n"
        "채팅 응답 카드의 장소 링크 클릭 시 카드에 표시된 장소명(예: '더포트', "
        "'바잇미', '반포 한강공원')을 그대로 query string 으로 전달하면 된다.\n"
        "정확 매칭(name 동등) → LIKE fallback 순서로 서울 한정 검색."
    ),
)
async def get_facility_by_name(
    name: Annotated[str, Query(min_length=1, description="장소명 원문 (URL 인코딩)")],
    db: AsyncSession = Depends(get_db),
) -> FacilityCard:
    """장소명으로 시설정보를 조회한다.

    Args:
        name: 카드에 표시된 장소명 (한글·공백 허용, URL 인코딩 자동 디코딩).
        db  : 비동기 DB 세션.

    Returns:
        `FacilityCard` 직렬화된 시설 상세.

    Raises:
        HTTPException: 일치하는 시설이 없으면 404.
    """
    facility = await lookup_facility_by_name(name, db)
    if facility is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 시설을 찾을 수 없습니다.",
        )

    return FacilityCard.model_validate(facility)
