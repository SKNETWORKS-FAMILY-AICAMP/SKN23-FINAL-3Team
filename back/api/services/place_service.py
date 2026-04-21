import logging

from sqlalchemy import or_, select
from models.place import Place as PlaceModel
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import Request

from core.type.place import PlaceType

logger = logging.getLogger(__name__)

_place_type = PlaceType()


async def search_places_from_db(
    query: str,
    db: AsyncSession,
    n_results: int = 5,
    category: str = None,
    city: str = None,
    request: Request = None,
) -> list[dict]:
    """하이브리드 장소 검색 (ChromaDB 벡터 검색 + RDB 상세 조회)

    1. 쿼리에서 지역명 자동 추출 (강남 → 강남구, 서울 → 서울특별시)
    2. ChromaDB에서 의미 기반 유사 장소 검색 → content_id 추출
    3. content_id로 RDB에서 상세 정보 조회 + 점수 계산
    4. ChromaDB 실패 시 RDB LIKE 검색으로 폴백

    Args:
        query: 검색 쿼리 (예: "강남 놀이터", "한강이랑 비슷한 분위기 장소")
        db: 비동기 DB 세션
        n_results: 반환할 최대 결과 수
        category: 카테고리 필터 (선택)
        city: 도시 필터 (선택, 쿼리에서 자동 추출되지 않은 경우 사용)
        request: FastAPI Request 객체 (AIContainer 접근용, 선택)

    Returns:
        장소 정보 dict 리스트. 예외 발생 시 빈 리스트 반환.
    """
    # ── 쿼리에서 지역명 자동 추출 ─────────────────────────
    location = _place_type.extract_location(query)
    if not city and location.get("city"):
        city = location["city"]
    district = location.get("district")

    # ── 1. ChromaDB 벡터 검색 ──────────────────────────────
    vector_results = []
    try:
        container = request.app.state.ai_container if request else None
        if container:
            vector_results = container._places_retriever.search(
                query=query,
                n_results=n_results,
                category=category,
                city=city,
                district=district,
            )
    except Exception as e:
        logger.warning(f"[PlaceService] ChromaDB 검색 실패, RDB 검색으로 전환: {e}")

    # ── 2. ChromaDB 결과 있으면 → content_id로 RDB 조회 ───
    if vector_results:
        try:
            content_ids = [
                vr["content_id"] for vr in vector_results
                if vr.get("content_id")
            ]
            if content_ids:
                stmt = select(PlaceModel).where(PlaceModel.content_id.in_(content_ids))
                result = await db.execute(stmt)
                db_places = {p.content_id: p for p in result.scalars().all()}

                places = []
                for vr in vector_results:
                    cid = vr.get("content_id", "")
                    if cid and cid in db_places:
                        place_dict = _to_dict(db_places[cid])
                        place_dict["rag_score"]   = vr.get("similarity", 0.0)
                        place_dict["rule_score"]  = _calc_rule_score(db_places[cid])
                        place_dict["final_score"] = round(
                            place_dict["rag_score"] * 0.7 +
                            place_dict["rule_score"] * 0.3, 4
                        )
                        places.append(place_dict)

                if places:
                    return sorted(places, key=lambda x: x["final_score"], reverse=True)

        except Exception as e:
            logger.warning(f"[PlaceService] RDB 상세 조회 실패, LIKE 검색으로 전환: {e}")

    # ── 3. 기존 LIKE 검색 (폴백) ───────────────────────────
    try:
        keyword = f"%{query}%"
        stmt = (
            select(PlaceModel)
            .where(or_(PlaceModel.name.like(keyword), PlaceModel.description.like(keyword)))
            .limit(n_results)
        )
        result = await db.execute(stmt)
        places = result.scalars().all()

        if not places:
            fallback_stmt = select(PlaceModel).order_by(PlaceModel.id.desc()).limit(n_results)
            fallback_result = await db.execute(fallback_stmt)
            places = fallback_result.scalars().all()

        return [_to_dict(p) for p in places]

    except Exception as e:
        logger.warning(f"[PlaceService] DB 장소 검색 실패: {e}")
        return []


def _calc_rule_score(place: PlaceModel) -> float:
    """규칙 기반 점수 계산

    반려견 동반 조건과 장소 특성을 기반으로 0~1 사이의 점수를 계산한다.
    - 전구역 동반 가능: +0.3
    - 실내외 정보 있음: +0.2

    Args:
        place: PlaceModel 인스턴스

    Returns:
        0.0 ~ 1.0 사이의 규칙 점수
    """
    score = 0.5
    if place.acmpy_type_cd and "전구역" in place.acmpy_type_cd:
        score += 0.3
    if place.is_indoor is not None:
        score += 0.2
    return round(min(score, 1.0), 4)


def _to_dict(place: PlaceModel) -> dict:
    """PlaceModel → dict 변환

    Args:
        place: PlaceModel 인스턴스

    Returns:
        프론트엔드에 전달할 장소 정보 dict
    """
    return {
        "name":        place.name or "",
        "address":     place.address or "",
        "category":    _place_type.get_type(place.content_type_id),
        "content_id":  place.content_id or "",
        "lat":         float(place.latitude) if place.latitude else 0.0,
        "lng":         float(place.longitude) if place.longitude else 0.0,
        "tel":         place.tel or "",
        "conditions":  place.acmpy_need_mtr or "",
        "indoor":      "Y" if place.is_indoor else "N",
        "outdoor":     "N" if place.is_indoor else "Y",
        "description": place.description or "",
        "firstimage":  place.firstimage or "",
        "similarity":  1.0,
        "rag_score":   0.0,
        "rule_score":  0.0,
        "final_score": 0.0,
    }
