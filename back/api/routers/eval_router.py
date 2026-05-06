"""평가 전용 라우터. 실서비스 /api/places/search 와 완전히 분리.

- 이미지 조회, 프로필 재순위, LLM 이유 생성 없이 장소 이름만 반환 (속도 최적화)
- search_mode / n_results 파라미터 노출 (ablation 실험용)
- 프로덕션 라우터(places_router.py)는 이 파일의 영향을 받지 않는다.
"""
import json

from core.deps import get_db
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from services.place_service import _parse_query_with_llm, search_places_from_db

router = APIRouter(tags=["Eval"])


@router.get("/parse")
async def eval_parse_query(
    query: str,
    request: Request,
):
    """쿼리를 파싱해서 결과를 반환 (ablation 사전 파싱용).

    Args:
        query: 사용자 검색 쿼리

    Returns:
        파싱된 조건 dict
    """
    parsed = await _parse_query_with_llm(query, request)
    return {
        "objective": parsed.objective,
        "subjective": parsed.subjective,
        "time_condition": parsed.time_condition,
        "use_current_location": parsed.use_current_location,
        "landmark": parsed.landmark,
    }


@router.get("/places/search")
async def eval_search_places(
    query: str,
    request: Request,
    mode: str = "combined",
    n: int = 5,
    parsed: str = None,
    db: AsyncSession = Depends(get_db),
):
    """Ablation 평가 전용 장소 검색.

    Args:
        query:  사용자 검색 쿼리
        mode:   "combined" | "rdb_only" | "rag_only"
        n:      반환할 장소 수 (최대 20)
        parsed: 사전 파싱된 쿼리 결과 JSON 문자열 (제공 시 LLM 파싱 생략)

    Returns:
        {"names": ["장소명1", "장소명2", ...]}
    """
    n = min(n, 20)
    pre_parsed = json.loads(parsed) if parsed else None
    places = await search_places_from_db(
        query, db, n_results=n, request=request, search_mode=mode, pre_parsed=pre_parsed
    )
    return {"names": [p["name"] for p in places if p.get("name")]}
