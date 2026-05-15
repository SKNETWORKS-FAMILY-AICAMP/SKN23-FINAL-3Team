import json
import logging
from urllib.parse import urlencode
from urllib.request import urlopen

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - only used in minimal runtimes.
    requests = None

from config import BASE_URL, REQUEST_TIMEOUT, SEARCH_ENDPOINT

logger = logging.getLogger(__name__)


class _SimpleResponse:
    def __init__(self, status: int, body: bytes) -> None:
        self.status = status
        self._body = body

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}: {self._body.decode('utf-8', errors='replace')}")

    def json(self) -> dict:
        return json.loads(self._body.decode("utf-8"))


def _get(url: str, params: dict, timeout: int):
    if requests is not None:
        return requests.get(url, params=params, timeout=timeout)

    query = urlencode(params, doseq=True)
    separator = "&" if "?" in url else "?"
    with urlopen(f"{url}{separator}{query}", timeout=timeout) as response:
        return _SimpleResponse(response.status, response.read())


def parse_query_eval(query: str) -> dict | None:
    """GET /api/eval/parse 호출 — 쿼리 파싱 결과 반환 (ablation 사전 파싱용).

    Returns:
        파싱된 조건 dict. 오류 시 None.
    """
    parse_endpoint = f"{BASE_URL}/api/eval/parse"
    try:
        resp = _get(
            parse_endpoint,
            params={"query": query},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        logger.warning("parse_query_eval failed for query=%r: %s", query, e)
        return None


def search_places(
    query: str,
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> list[str]:
    """GET /api/places/search 호출 후 장소 이름 목록(최대 5개) 반환.

    Returns:
        장소 이름 리스트. 오류 시 예외를 그대로 전파.
    """
    params = {"query": query}
    if user_lat is not None and user_lng is not None:
        params["user_lat"] = user_lat
        params["user_lng"] = user_lng

    resp = _get(
        SEARCH_ENDPOINT,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    places = data.get("places", [])
    names = [p["name"] for p in places if p.get("name")]
    logger.debug("query=%r -> %d results: %s", query, len(names), names)
    return names


def search_places_eval(
    query: str,
    n_results: int = 5,
    mode: str = "combined",
    parsed: dict = None,
    user_lat: float | None = None,
    user_lng: float | None = None,
    debug: bool = False,
    return_payload: bool = False,
) -> list[str]:
    """GET /api/eval/places/search 호출 — ablation 평가 전용.

    Args:
        query:     사용자 검색 쿼리
        n_results: 반환받을 최대 장소 수 (최대 20)
        mode:      검색 모드 — "combined" | "rdb_only" | "rag_only"
        parsed:    사전 파싱된 쿼리 결과 dict (제공 시 서버에서 LLM 파싱 생략)
        user_lat/user_lng: GPS 질문일 때만 전달하는 고정 사용자 좌표

    Returns:
        장소 이름 리스트. 오류 시 예외를 그대로 전파.
    """
    eval_endpoint = f"{BASE_URL}/api/eval/places/search"
    params: dict = {
        "query": query,
        "n": n_results,
        "mode": mode,
    }
    if debug:
        params["debug"] = "true"
    if user_lat is not None and user_lng is not None:
        params["user_lat"] = user_lat
        params["user_lng"] = user_lng
    if parsed is not None:
        params["parsed"] = json.dumps(parsed, ensure_ascii=False)
    resp = _get(
        eval_endpoint,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    names = data.get("names", [])
    logger.debug("eval query=%r mode=%s n=%d -> %d results", query, mode, n_results, len(names))
    if return_payload:
        return data
    return names


def search_places_eval_with_profile(
    query: str,
    dog_tags: list[str] | None = None,
    owner_tags: list[str] | None = None,
    n_results: int = 20,
    mode: str = "combined",
    parsed: dict | None = None,
    user_lat: float | None = None,
    user_lng: float | None = None,
) -> list[dict]:
    """Call the eval search endpoint with an explicit dog/owner profile.

    The normal place-search API loads tags from the logged-in user's DB state.
    Trait evaluation needs every spreadsheet row to supply its own profile, so
    this client uses the eval endpoint parameters added for offline evaluation.
    """
    eval_endpoint = f"{BASE_URL}/api/eval/places/search"
    params: dict = {
        "query": query,
        "n": n_results,
        "mode": mode,
    }
    if dog_tags:
        params["dog_tags"] = ";".join(dog_tags)
    if owner_tags:
        params["owner_tags"] = ";".join(owner_tags)
    if parsed is not None:
        params["parsed"] = json.dumps(parsed, ensure_ascii=False)
    if user_lat is not None and user_lng is not None:
        params["user_lat"] = user_lat
        params["user_lng"] = user_lng

    resp = _get(
        eval_endpoint,
        params=params,
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    places = data.get("places", [])
    logger.debug(
        "trait eval query=%r dog=%s owner=%s n=%d -> %d results",
        query,
        dog_tags,
        owner_tags,
        n_results,
        len(places),
    )
    return places
