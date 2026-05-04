from typing import Annotated
from core.deps import get_current_user, get_db
from models.user import User
from schemas.chat_message import FacilityCard
from schemas.place import (
    PlaceFavoriteItem,
    PlaceFavoriteResponse,
    PlaceFavoriteToggleResponse,
)
from sqlalchemy.ext.asyncio import AsyncSession
from services.place_image_service import enrich_place_images
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from services.place_service import (lookup_facility_by_name, search_places_from_db)
from services import favorite_place_service as fav_svc
from services.chat_response_service import (DispatchContext, _load_place_preference_context, _rerank_places_with_profile, generate_place_reasons)

router = APIRouter(tags=["places"])

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


@router.get(
    "/favorites",
    response_model=PlaceFavoriteResponse,
    summary="즐겨찾기 장소 목록 조회",
    description=(
        "현재 로그인 사용자의 즐겨찾기 장소 목록을 반환한다.\n\n"
        "응답 항목은 카드 식별·정렬에 필요한 최소 필드(`content_id`, `name`, "
        "`sub_category`, `favorited_at`)만 포함한다. 이미지·주소 등 추가 정보는 "
        "프론트가 별도 API(예: `/api/places/by-name?name=`)로 보강.\n\n"
        "정렬: `favorited_at DESC` (최근 추가가 위)."
    ),
)
async def list_favorite_places(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlaceFavoriteResponse:
    items = await fav_svc.list_favorite_places(db, current_user.id)
    return PlaceFavoriteResponse(
        items=[PlaceFavoriteItem(**item) for item in items],
    )


@router.patch(
    "/{content_id}/favorite",
    response_model=PlaceFavoriteToggleResponse,
    summary="장소 즐겨찾기 토글",
    description=(
        "장소 즐겨찾기를 토글한다 — 미등록이면 INSERT, 등록되어 있으면 DELETE.\n\n"
        "**입력**: 한국관광공사 콘텐츠 ID(`content_id`, 카드가 보유한 키).\n"
        "**중복 차단**: DB UNIQUE (user_id, place_id)로 강제.\n"
        "**일일 제한 없음** (다이어리 즐겨찾기와 차이)."
    ),
)
async def toggle_favorite_place(
    content_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PlaceFavoriteToggleResponse:
    is_favorite, favorite = await fav_svc.toggle_favorite_place(
        content_id, db, current_user.id
    )
    return PlaceFavoriteToggleResponse(
        content_id=content_id,
        is_favorite=is_favorite,
        favorited_at=favorite.created_at if favorite else None,
    )
