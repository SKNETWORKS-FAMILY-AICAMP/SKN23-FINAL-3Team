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
