import logging

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.place import Place as PlaceModel

logger = logging.getLogger(__name__)


async def search_places_from_db(
    query: str,
    db: AsyncSession,
    n_results: int = 5,
) -> list[dict]:
    """places 테이블에서 쿼리 키워드로 LIKE 검색 후 결과를 반환한다.

    결과가 없으면 최근 등록된 장소 n_results개를 반환하여
    파이프라인이 항상 응답을 반환할 수 있도록 보장한다.

    Args:
        query: 검색 키워드 (name 또는 description 컬럼에 LIKE 매칭).
        db: 비동기 DB 세션.
        n_results: 반환할 최대 결과 수.

    Returns:
        장소 정보 dict 리스트. 예외 발생 시 빈 리스트 반환.
    """
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


def _to_dict(place: PlaceModel) -> dict:
    return {
        "name": place.name or "",
        "address": place.address or "",
        "category": place.content_type_id or "",
        "lat": float(place.latitude) if place.latitude else 0.0,
        "lng": float(place.longitude) if place.longitude else 0.0,
        "tel": place.tel or "",
        "conditions": place.acmpy_need_mtr or "",
        "indoor": "Y" if place.is_indoor else "N",
        "outdoor": "N" if place.is_indoor else "Y",
        "description": place.description or "",
        "firstimage": place.firstimage or "",
        "similarity": 1.0,
    }
