import logging

import requests

from config import REQUEST_TIMEOUT, SEARCH_ENDPOINT

logger = logging.getLogger(__name__)


def search_places(query: str) -> list[str]:
    """GET /api/places/search 호출 후 장소 이름 목록(최대 5개) 반환.

    Returns:
        장소 이름 리스트. 오류 시 예외를 그대로 전파.
    """
    resp = requests.get(
        SEARCH_ENDPOINT,
        params={"query": query},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    places = data.get("places", [])
    names = [p["name"] for p in places if p.get("name")]
    logger.debug("query=%r -> %d results: %s", query, len(names), names)
    return names


def search_places_eval(query: str, n_results: int = 5, mode: str = "combined") -> list[str]:
    """GET /api/eval/places/search 호출 — ablation 평가 전용.

    Args:
        query:     사용자 검색 쿼리
        n_results: 반환받을 최대 장소 수 (최대 20)
        mode:      검색 모드 — "combined" | "rdb_only" | "rag_only"

    Returns:
        장소 이름 리스트. 오류 시 예외를 그대로 전파.
    """
    from config import BASE_URL
    eval_endpoint = f"{BASE_URL}/api/eval/places/search"
    resp = requests.get(
        eval_endpoint,
        params={"query": query, "n": n_results, "mode": mode},
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    names = data.get("names", [])
    logger.debug("eval query=%r mode=%s n=%d -> %d results", query, mode, n_results, len(names))
    return names
