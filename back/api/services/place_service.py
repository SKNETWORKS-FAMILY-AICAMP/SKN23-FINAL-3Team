import logging
import re
from copy import deepcopy
from dataclasses import dataclass

import httpx
from fastapi import Request
from sqlalchemy import and_, func, not_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.type.place import PlaceType
from models.place import Place as PlaceModel

logger = logging.getLogger(__name__)

_place_type = PlaceType()

KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
LANDMARK_RADIUS_M = 1000
LANDMARK_RADIUS_STEPS_M = (1000, 2000, 3000)
LANDMARK_MIN_RESULTS = 3

SEOUL = "서울특별시"
NO_INFO = "정보없음"
ALWAYS_OPEN = "연중무휴"
OPEN_24H = "24시간"
HOLIDAY = "법정공휴일"
SUNDAY = "일요일"
DAILY = "매일"
EARLY_MORNING = "이른아침"
MORNING = "오전"
LUNCH = "점심"
EVENING = "저녁"
NIGHT = "밤"
WEEKEND = "주말"
FULL_ZONE = "전구역"
NO_RESTRICTION = "제한사항 없음"
OUTING_SUBCATEGORIES = {"공원", "관광지", "반려견놀이터", "카페", "식당"}
DEPRIORITIZED_SUBCATEGORIES = {"동물병원", "동물약국", "미용", "위탁관리"}
EXPLICIT_PURPOSE_KEYWORDS = (
    "병원",
    "약국",
    "미용",
    "위탁",
    "호텔",
    "펜션",
    "카페",
    "식당",
    "공원",
    "놀이터",
    "관광지",
    "박물관",
    "미술관",
    "문예회관",
    "용품",
)


PET_SIZE_CONTEXT_WORDS = ("반려견", "강아지", "개", "아이", "댕댕이", "견")
PLACE_SIZE_CONTEXT_WORDS = ("카페", "식당", "공원", "숙소", "호텔", "펜션", "놀이터", "공간", "매장")

OUT_OF_SERVICE_KEYWORDS = (
    "제주", "부산", "강원", "경주", "속초", "동해", "인천", "수원", "대전",
    "가평", "경기", "충청", "전라", "경상", "울산", "광주", "대구", "세종",
    "춘천", "강릉", "여수", "통영", "거제", "포항", "안동", "전주", "청주",
    "해운대", "제주도", "고양", "성남", "용인", "평택", "화성",
)


class ParsedQuery:
    """Container for parsed place-search query conditions."""

    def __init__(self, raw_query: str):
        self.raw_query = raw_query
        self.objective: dict = {
            "city": SEOUL,
            "district": None,
            "sub_category": None,
            "is_indoor": None,
            "is_outdoor": None,
            "has_parking": None,
            "pet_zone_type": None,
            "pet_size_limit": None,
            "entrance_fee_preference": None,
            "extra_fee_preference": None,
            "waste_bag_preference": None,
        }
        self.subjective: str = raw_query
        self.time_condition: str | None = None
        self.landmark: str | None = None
        self.landmark_coords: tuple[float, float] | None = None


def _extract_restriction_tags(text: str | None) -> set[str]:
    """Normalize free-form pet restriction text into lightweight tags."""
    raw = (text or "").strip()
    if not raw:
        return {"no_restrictions"}

    normalized = raw.replace(" ", "")
    tags: set[str] = set()

    if NO_RESTRICTION in raw:
        tags.add("no_restrictions")
    if "목줄" in raw:
        tags.add("leash_required")
    if "배변봉투" in raw:
        if any(token in raw for token in ("제공", "비치", "구비", "무료")):
            tags.add("waste_bag_provided")
        else:
            tags.add("waste_bag_required")
    if any(token in normalized for token in ("실내만", "실내에서만")):
        tags.add("indoor_only")
    if any(token in normalized for token in ("실외만", "야외만")):
        tags.add("outdoor_only")
    if "테라스" in raw:
        tags.add("terrace_only")
    if FULL_ZONE in raw:
        tags.add("full_zone_allowed")
    if "소형견" in raw:
        tags.add("small_dogs_only")
    if "중형견" in raw:
        tags.add("medium_dogs_allowed")
    if "대형견" in raw:
        tags.add("large_dogs_allowed")

    return tags or {"no_restrictions"}


def _get_restriction_preferences(parsed: ParsedQuery) -> dict[str, object]:
    """Interpret raw query intent into common restriction preferences."""
    query = (parsed.raw_query or "").strip()
    forbidden_tags: set[str] = set()
    preferred_tags: set[str] = set()
    focus: str | None = None

    if parsed.objective.get("waste_bag_preference") == "provided_or_not_required":
        forbidden_tags.add("waste_bag_required")
        preferred_tags.update({"waste_bag_provided", "no_restrictions"})
        focus = "waste_bag"

    leash_free_patterns = (
        r"\ubaa9\uc904.*(\uc5c6\uc774|\ud480\uace0|\uc790\uc720\ub86d\uac8c)",
        r"(\uc5c6\uc774|\ud480\uace0|\uc790\uc720\ub86d\uac8c).*?\ubaa9\uc904",
        r"\ub178\ub9ac\ub4dc",
    )
    if any(re.search(pattern, query) for pattern in leash_free_patterns):
        forbidden_tags.add("leash_required")
        preferred_tags.update({"full_zone_allowed", "no_restrictions"})
        focus = "leash"

    return {
        "forbidden_tags": forbidden_tags,
        "preferred_tags": preferred_tags,
        "focus": focus,
    }


def _relax_objective_for_restriction_focus(parsed: ParsedQuery) -> None:
    """Avoid over-constraining searches when the user's main intent is a restriction."""
    prefs = _get_restriction_preferences(parsed)
    focus = prefs.get("focus")
    if not focus or _has_explicit_place_purpose(parsed.raw_query):
        return

    relaxed = []
    if parsed.objective.get("sub_category") == "반려견놀이터":
        parsed.objective["sub_category"] = None
        relaxed.append("sub_category")
    if parsed.objective.get("pet_zone_type") == FULL_ZONE:
        parsed.objective["pet_zone_type"] = None
        relaxed.append("pet_zone_type")

    if relaxed:
        logger.info(
            "[PlaceService] restriction-focused query: relaxed %s before candidate filtering",
            ", ".join(relaxed),
        )


def _has_pet_size_context(query: str) -> bool:
    if not query:
        return False

    pattern = r"(소형|중형|대형|작은|큰)\s*(반려견|강아지|개|아이|댕댕이|견)"
    reverse_pattern = r"(반려견|강아지|개|아이|댕댕이|견)\s*(이|가|도|랑|와|하고|과)?\s*(소형|중형|대형|작은|큰)"
    return bool(re.search(pattern, query) or re.search(reverse_pattern, query))


def _has_place_size_context(query: str) -> bool:
    if not query:
        return False

    pattern = r"(소형|중형|대형|작은|큰|넓은)\s*(카페|식당|공원|숙소|호텔|펜션|놀이터|공간|매장)"
    reverse_pattern = r"(카페|식당|공원|숙소|호텔|펜션|놀이터|공간|매장)\s*(이|가|도|를|을)?\s*(소형|중형|대형|작은|큰|넓은)"
    return bool(re.search(pattern, query) or re.search(reverse_pattern, query))


def _normalize_size_interpretation(parsed: ParsedQuery) -> None:
    """Disambiguate whether size words refer to pet size or place size."""
    pet_size = (parsed.objective.get("pet_size_limit") or "").strip()
    if not pet_size:
        return

    query = parsed.raw_query or ""
    if _has_pet_size_context(query):
        return

    if _has_place_size_context(query):
        parsed.objective["pet_size_limit"] = None
        subjective = (parsed.subjective or "").strip()
        if not subjective:
            parsed.subjective = "넓은 공간"
        elif "넓은 공간" not in subjective:
            parsed.subjective = f"{subjective}, 넓은 공간"
        logger.info(
            f"[PlaceService] size disambiguation: '{pet_size}' interpreted as place size"
        )


def _normalize_fee_preferences(parsed: ParsedQuery) -> None:
    """Interpret fee-related expressions into structured preferences."""
    query = (parsed.raw_query or "").strip()
    if not query:
        return

    entrance_patterns = (
        r"(입장료|이용료)\s*(없이|없는|안\s*드는|안드는|무료)",
        r"(무료\s*입장|무료로\s*입장)",
    )
    extra_patterns = (
        r"(추가\s*(비용|요금|금액)|애견\s*동반\s*추가\s*요금)\s*(없이|없는|없나요|없고|무료)",
        r"(추가비용\s*없이|추가요금\s*없이|추가\s*비용\s*없이)",
    )

    broad_cost_patterns = (
        r"\ucd94\uac00\s*\ube44\uc6a9\s*\uc5c6\uc774",
        r"\ube44\uc6a9\s*\uc5c6\uc774",
        r"\ubb34\ub8cc\ub85c",
        r"\ub3c8\s*\uc548\s*\ub4e4",
    )
    explicit_pet_extra_patterns = (
        r"\uac15\uc544\uc9c0\s*\ucd94\uac00\s*\uc694\uae08",
        r"\uc560\uacac\s*\ub3d9\ubc18\s*\ucd94\uac00\s*\uc694\uae08",
        r"\ubc18\ub824\uacac\s*\ub3d9\ubc18\s*\ucd94\uac00\s*\uc694\uae08",
    )

    if any(re.search(pattern, query) for pattern in entrance_patterns):
        parsed.objective["entrance_fee_preference"] = "free_only"

    if any(re.search(pattern, query) for pattern in broad_cost_patterns):
        parsed.objective["entrance_fee_preference"] = "free_only"
        parsed.objective["extra_fee_preference"] = "no_extra_fee"
    elif any(re.search(pattern, query) for pattern in explicit_pet_extra_patterns) or any(
        re.search(pattern, query) for pattern in extra_patterns
    ):
        parsed.objective["extra_fee_preference"] = "no_extra_fee"


def _normalize_supply_preferences(parsed: ParsedQuery) -> None:
    """Interpret supply-related expressions into structured preferences."""
    query = (parsed.raw_query or "").strip()
    if not query:
        return

    waste_bag_patterns = (
        r"\ubc30\ubcc0\ubd09\ud22c.*(\uc548\s*\ucc59\uae30|(\ub530\ub85c\s*)?\uc5c6\uc774|\uc81c\uacf5|\ube44\uce58|\uad6c\ube44)",
        r"(\uc548\s*\ucc59\uae30|(\ub530\ub85c\s*)?\uc5c6\uc774).*?\ubc30\ubcc0\ubd09\ud22c",
    )
    if any(re.search(pattern, query) for pattern in waste_bag_patterns):
        parsed.objective["waste_bag_preference"] = "provided_or_not_required"
        logger.info("[PlaceService] supply preference detected: waste bags provided or not required")


def _normalize_indoor_outdoor_subjective(parsed: ParsedQuery) -> None:
    """실내/실외 조건이 파싱된 경우 subjective 텍스트에도 반영해 임베딩 품질을 높인다."""
    is_indoor = parsed.objective.get("is_indoor")
    is_outdoor = parsed.objective.get("is_outdoor")
    subjective = (parsed.subjective or "").strip()

    if is_indoor is True and "실내" not in subjective:
        parsed.subjective = f"실내 {subjective}".strip()
        logger.info("[PlaceService] indoor condition injected into subjective")
    elif is_outdoor is True and not any(kw in subjective for kw in ("실외", "야외")):
        parsed.subjective = f"야외 실외 {subjective}".strip()
        logger.info("[PlaceService] outdoor condition injected into subjective")


def _has_fee_preferences(parsed: ParsedQuery) -> bool:
    return bool(
        parsed.objective.get("entrance_fee_preference")
        or parsed.objective.get("extra_fee_preference")
    )


def _is_free_like(value: str | None) -> bool:
    text = (value or "").strip()
    if not text:
        return False

    lowered = text.lower()
    free_tokens = ("없음", "해당없음", "무료", "무료입장", "0원")
    return any(token in text for token in free_tokens) or any(
        token in lowered for token in ("free", "no fee", "free entry")
    )


def _is_free_like_strict(value: str | None) -> bool:
    text = (value or "").strip()
    if not text:
        return False

    normalized = text.replace(",", "").replace(" ", "")
    lowered = normalized.lower()

    amount_match = re.search(r"(\d+)\s*원", normalized)
    if amount_match:
        try:
            return int(amount_match.group(1)) == 0
        except ValueError:
            return False

    exact_free_tokens = {
        "없음",
        "해당없음",
        "무료",
        "무료입장",
        "0원",
    }
    exact_free_english = {"free", "nofee", "freeentry"}
    non_free_tokens = {"변동", "변동있음", "별도문의", "문의", "확인"}

    if normalized in exact_free_tokens or lowered in exact_free_english:
        return True
    if normalized in non_free_tokens:
        return False

    return False


def _matches_fee_preferences(candidate: dict, parsed: ParsedQuery) -> bool:
    entrance_pref = parsed.objective.get("entrance_fee_preference")
    extra_pref = parsed.objective.get("extra_fee_preference")

    entrance_fee = candidate.get("entrance_fee", "")
    extra_fee = candidate.get("extra_fee", "")

    if entrance_pref == "free_only" and not _is_free_like_v2(entrance_fee):
        return False
    if extra_pref == "no_extra_fee" and not _is_free_like_v2(extra_fee):
        return False

    return True


def _is_free_like_v2(value: str | None) -> bool:
    text = (value or "").strip()
    if not text:
        return False

    normalized = text.replace(",", "").replace(" ", "")
    lowered = normalized.lower()

    amount_match = re.search(r"(\d+)\s*\uc6d0", normalized)
    if amount_match:
        try:
            return int(amount_match.group(1)) == 0
        except ValueError:
            return False

    exact_free_tokens = {
        "\uc5c6\uc74c",
        "\ud574\ub2f9\uc5c6\uc74c",
        "\ubb34\ub8cc",
        "\ubb34\ub8cc\uc785\uc7a5",
        "0\uc6d0",
    }
    exact_free_english = {"free", "nofee", "freeentry"}
    non_free_tokens = {
        "\ubcc0\ub3d9",
        "\ubcc0\ub3d9\uc788\uc74c",
        "\ubcc4\ub3c4\ubb38\uc758",
        "\ubb38\uc758",
        "\ud655\uc778",
    }

    if normalized in exact_free_tokens or lowered in exact_free_english:
        return True
    if normalized in non_free_tokens:
        return False

    return False


def _apply_fee_hard_filter(
    places: list[dict],
    parsed: ParsedQuery,
    *,
    source: str,
) -> list[dict]:
    """Apply a final fee-based guard before returning results."""
    if not _has_fee_preferences(parsed):
        return places

    kept: list[dict] = []
    for place in places:
        entrance_fee = place.get("entrance_fee", "")
        extra_fee = place.get("extra_fee", "")
        matched = _matches_fee_preferences(place, parsed)
        logger.info(
            "[PlaceService] fee hard filter (%s): %s | entrance_fee=%s | extra_fee=%s | matched=%s",
            source,
            place.get("name", ""),
            entrance_fee or "<empty>",
            extra_fee or "<empty>",
            matched,
        )
        if matched:
            kept.append(place)

    logger.info(
        "[PlaceService] fee hard filter (%s): %s -> %s",
        source,
        len(places),
        len(kept),
    )
    return kept


def _matches_restriction_preferences(candidate: dict, parsed: ParsedQuery) -> bool:
    prefs = _get_restriction_preferences(parsed)
    forbidden_tags = prefs["forbidden_tags"]
    if not forbidden_tags:
        return True

    tags = set(candidate.get("restriction_tags") or [])
    return not any(tag in tags for tag in forbidden_tags)


def _apply_restriction_hard_filter(
    places: list[dict],
    parsed: ParsedQuery,
    *,
    source: str,
) -> list[dict]:
    """Apply a final restriction-based guard using normalized condition tags."""
    prefs = _get_restriction_preferences(parsed)
    forbidden_tags = prefs["forbidden_tags"]
    if not forbidden_tags:
        return places

    kept: list[dict] = []
    for place in places:
        tags = set(place.get("restriction_tags") or [])
        matched = _matches_restriction_preferences(place, parsed)
        logger.info(
            "[PlaceService] restriction hard filter (%s): %s | tags=%s | matched=%s",
            source,
            place.get("name", ""),
            sorted(tags),
            matched,
        )
        if matched:
            kept.append(place)

    logger.info(
        "[PlaceService] restriction hard filter (%s): %s -> %s",
        source,
        len(places),
        len(kept),
    )
    return kept


async def _parse_query_with_llm(query: str, request: Request = None) -> ParsedQuery:
    """Parse the raw query into objective and subjective fields."""
    parsed = ParsedQuery(query)

    location = _place_type.extract_location(query)
    if location.get("city"):
        parsed.objective["city"] = location["city"]
    if location.get("district"):
        parsed.objective["district"] = location["district"]

    try:
        container = request.app.state.ai_container if request else None
        if container and hasattr(container, "_query_parser"):
            result = await container._query_parser.parse(query)
            for key in parsed.objective:
                if result.get(key) is not None:
                    parsed.objective[key] = result[key]
            parsed.subjective = result.get("subjective", query)
            parsed.time_condition = result.get("time_condition")
            parsed.landmark = result.get("landmark")
            _normalize_size_interpretation(parsed)
    except Exception as e:
        logger.warning(f"[PlaceService] LLM query parsing failed, using defaults: {e}")

    _normalize_fee_preferences(parsed)
    _normalize_supply_preferences(parsed)
    _relax_objective_for_restriction_focus(parsed)
    _normalize_indoor_outdoor_subjective(parsed)
    return parsed


def _clone_parsed(parsed: ParsedQuery) -> ParsedQuery:
    cloned = ParsedQuery(parsed.raw_query)
    cloned.objective = deepcopy(parsed.objective)
    cloned.subjective = parsed.subjective
    cloned.time_condition = parsed.time_condition
    cloned.landmark = getattr(parsed, "landmark", None)
    cloned.landmark_coords = getattr(parsed, "landmark_coords", None)
    return cloned


def _has_explicit_place_purpose(query: str) -> bool:
    """Return True when the user clearly names a specific place type."""
    return any(keyword in (query or "") for keyword in EXPLICIT_PURPOSE_KEYWORDS)


def _should_prioritize_outing(parsed: ParsedQuery) -> bool:
    """Use outing-first ranking only for broad recommendation questions."""
    return (
        not parsed.objective.get("sub_category")
        and not _has_explicit_place_purpose(parsed.raw_query)
    )


def _calc_category_bias(place: PlaceModel, parsed: ParsedQuery) -> float:
    """Add a small ranking bias for outing-friendly categories on broad queries."""
    sub_category = (place.sub_category or "").strip()
    bias = 0.0
    restriction_tags = _extract_restriction_tags(place.pet_restrictions)
    restriction_focus = _get_restriction_preferences(parsed).get("focus")

    if _should_prioritize_outing(parsed):
        if sub_category in OUTING_SUBCATEGORIES:
            bias += 0.25
        elif sub_category in DEPRIORITIZED_SUBCATEGORIES:
            bias -= 0.25

    if parsed.objective.get("waste_bag_preference") == "provided_or_not_required":
        if sub_category in OUTING_SUBCATEGORIES:
            bias += 0.2
        elif sub_category in {"반려동물용품", "동물병원", "동물약국", "미용", "위탁관리"}:
            bias -= 0.35
        if "waste_bag_provided" in restriction_tags:
            bias += 0.15

    if restriction_focus == "leash":
        if "leash_required" in restriction_tags:
            bias -= 0.6
        elif sub_category in {"반려견놀이터", "카페", "식당"}:
            bias += 0.1
        elif sub_category in {"공원", "관광지"} and "full_zone_allowed" not in restriction_tags:
            bias -= 0.15

    return bias


def _apply_outing_priority(
    places: list[dict],
    parsed: ParsedQuery,
    n_results: int,
) -> list[dict]:
    """Prefer outing-friendly categories first for broad recommendation queries."""
    if not _should_prioritize_outing(parsed):
        return sorted(places, key=lambda x: x["final_score"], reverse=True)[:n_results]

    outing: list[dict] = []
    neutral: list[dict] = []
    deprioritized: list[dict] = []

    for place in places:
        sub_category = (place.get("sub_category") or "").strip()
        if sub_category in OUTING_SUBCATEGORIES:
            outing.append(place)
        elif sub_category in DEPRIORITIZED_SUBCATEGORIES:
            deprioritized.append(place)
        else:
            neutral.append(place)

    key_fn = lambda x: x["final_score"]
    outing = sorted(outing, key=key_fn, reverse=True)
    neutral = sorted(neutral, key=key_fn, reverse=True)
    deprioritized = sorted(deprioritized, key=key_fn, reverse=True)

    prioritized = outing + neutral + deprioritized
    return prioritized[:n_results]


async def _get_landmark_coords(landmark: str) -> tuple[float, float] | None:
    """Resolve landmark coordinates via Kakao keyword search."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(
                KAKAO_GEOCODE_URL,
                headers={"Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}"},
                params={"query": landmark, "size": 1},
            )
            docs = resp.json().get("documents", [])
            if docs:
                lat = float(docs[0]["y"])
                lng = float(docs[0]["x"])
                logger.info(f"[PlaceService] landmark coords: {landmark} -> ({lat}, {lng})")
                return lat, lng
    except Exception as e:
        logger.warning(f"[PlaceService] landmark lookup failed ({landmark}): {e}")
    return None


async def _filter_by_rdb(
    parsed: ParsedQuery,
    db: AsyncSession,
    max_candidates: int = 200,
) -> list[str]:
    """Filter candidates from RDB using objective conditions."""
    obj = parsed.objective
    conditions = []

    if obj.get("city"):
        conditions.append(PlaceModel.address.like(f"%{obj['city']}%"))
    if obj.get("district"):
        conditions.append(PlaceModel.address.like(f"%{obj['district']}%"))
    if obj.get("sub_category"):
        conditions.append(PlaceModel.sub_category == obj["sub_category"])
    if obj.get("is_indoor") is not None:
        conditions.append(PlaceModel.is_indoor == obj["is_indoor"])
    if obj.get("is_outdoor") is not None:
        conditions.append(PlaceModel.is_outdoor == obj["is_outdoor"])
    if obj.get("has_parking"):
        conditions.append(PlaceModel.has_parking == obj["has_parking"])
    if obj.get("pet_zone_type"):
        conditions.append(PlaceModel.pet_zone_type == obj["pet_zone_type"])
    if obj.get("pet_size_limit"):
        conditions.append(PlaceModel.pet_size_limit.like(f"%{obj['pet_size_limit']}%"))
    if obj.get("waste_bag_preference") == "provided_or_not_required":
        conditions.append(
            not_(
                and_(
                    PlaceModel.pet_restrictions.isnot(None),
                    PlaceModel.pet_restrictions.like("%\ubc30\ubcc0\ubd09\ud22c%"),
                    not_(
                        or_(
                            PlaceModel.pet_restrictions.like("%\uc81c\uacf5%"),
                            PlaceModel.pet_restrictions.like("%\ube44\uce58%"),
                            PlaceModel.pet_restrictions.like("%\ubb34\ub8cc%"),
                        )
                    ),
                )
            )
        )

    def _landmark_conditions(radius_m: int) -> list:
        lat, lng = parsed.landmark_coords
        return [
            PlaceModel.latitude.isnot(None),
            PlaceModel.longitude.isnot(None),
            func.ST_Distance_Sphere(
                func.point(PlaceModel.longitude, PlaceModel.latitude),
                func.point(lng, lat),
            ) <= radius_m,
        ]

    async def _execute(extra_conditions: list | None = None) -> list[str]:
        all_conditions = conditions + (extra_conditions or [])
        stmt = (
            select(PlaceModel.content_id)
            .where(and_(*all_conditions) if all_conditions else True)
            .limit(max_candidates)
        )
        result = await db.execute(stmt)
        return [row[0] for row in result.fetchall()]

    if parsed.landmark_coords:
        content_ids = []
        for radius_m in LANDMARK_RADIUS_STEPS_M:
            content_ids = await _execute(_landmark_conditions(radius_m))
            logger.info(
                f"[PlaceService] landmark radius {radius_m}m -> {len(content_ids)} candidates"
            )
            if (
                len(content_ids) >= LANDMARK_MIN_RESULTS
                or radius_m == LANDMARK_RADIUS_STEPS_M[-1]
            ):
                break
    else:
        content_ids = await _execute()

    logger.info(
        f"[PlaceService] RDB filter result: {len(content_ids)} "
        f"(conditions: {obj}, landmark: {parsed.landmark})"
    )
    return content_ids


def _parse_operation_hours(operation_info: str) -> dict:
    """Parse operation_info into comparable hour and closure flags."""
    if not operation_info or NO_INFO in operation_info:
        return {}

    result = {}

    hours_part = operation_info.split("/")[0] if "/" in operation_info else operation_info
    closed_part = operation_info.split("/")[1] if "/" in operation_info else ""

    result["always_open"] = ALWAYS_OPEN in closed_part
    result["is_24hours"] = OPEN_24H in hours_part
    result["closed_on_holiday"] = HOLIDAY in closed_part and not result["always_open"]
    result["closed_on_sat"] = "토" in closed_part and not result["always_open"]
    result["closed_on_sun"] = (
        ("일" in closed_part or SUNDAY in closed_part) and not result["always_open"]
    )

    matches = re.findall(r"(\d{1,2}):(\d{2})~(\d{1,2}):(\d{2})", hours_part)
    if matches:
        open_times, close_times = [], []
        for oh, om, ch, cm in matches:
            open_times.append(int(oh) * 100 + int(om))
            close_h = int(ch)
            if close_h < 6:
                close_h += 24
            close_times.append(close_h * 100 + int(cm))
        result["earliest_open"] = min(open_times)
        result["latest_close"] = max(close_times)

    if result["is_24hours"]:
        result["earliest_open"] = 0
        result["latest_close"] = 2400

    result["has_sat"] = "토" in hours_part
    result["has_sun"] = "일" in hours_part or DAILY in hours_part
    result["has_weekend"] = result["has_sat"] or result["has_sun"]

    return result


def _check_time_condition(operation_info: str | None, time_condition: str) -> bool:
    """Return True when a place satisfies the requested time condition."""
    if not time_condition:
        return True
    if not operation_info or NO_INFO in operation_info:
        return True

    h = _parse_operation_hours(operation_info)
    if not h:
        return True

    earliest = h.get("earliest_open", 2400)
    latest = h.get("latest_close", 0)

    if time_condition == EARLY_MORNING:
        return earliest <= 900
    if time_condition == MORNING:
        return earliest <= 1000
    if time_condition == LUNCH:
        return earliest <= 1200 and latest >= 1300
    if time_condition == EVENING:
        return latest >= 1800
    if time_condition == NIGHT:
        return latest >= 2200
    if time_condition == OPEN_24H:
        return h.get("is_24hours", False) or latest >= 2400
    if time_condition == ALWAYS_OPEN:
        return h.get("always_open", False)
    if time_condition == WEEKEND:
        return h.get("has_weekend", False)
    if time_condition == HOLIDAY:
        return not h.get("closed_on_holiday", True)

    return True


async def _filter_by_time(
    candidate_ids: list[str],
    time_condition: str | None,
    db: AsyncSession,
) -> list[str]:
    """Filter candidate IDs by time condition, keeping original on empty result."""
    if not time_condition or not candidate_ids:
        return candidate_ids

    stmt = select(PlaceModel.content_id, PlaceModel.operation_info).where(
        PlaceModel.content_id.in_(candidate_ids)
    )
    result = await db.execute(stmt)
    rows = result.fetchall()

    filtered = [cid for cid, op_info in rows if _check_time_condition(op_info, time_condition)]

    if not filtered:
        logger.info(f"[PlaceService] time filter ({time_condition}) -> 0, keep original")
        return candidate_ids

    logger.info(
        f"[PlaceService] time filter ({time_condition}): "
        f"{len(candidate_ids)} -> {len(filtered)}"
    )
    return filtered


async def _search_by_chromadb(
    parsed: ParsedQuery,
    candidate_ids: list[str],
    n_results: int,
    request: Request = None,
) -> list[dict]:
    """Run Chroma similarity search for the subjective part of the query."""
    try:
        container = request.app.state.ai_container if request else None
        if not container:
            return []

        query_text = (parsed.subjective or "").strip() or parsed.raw_query

        # candidate_ids가 있으면 후처리 필터를 위해 여유롭게 더 가져온다
        has_candidates = bool(candidate_ids)
        fetch_n = max(n_results, 50) if has_candidates else n_results
        search_n_results = max(fetch_n, 20) if _has_fee_preferences(parsed) else fetch_n

        results = container._places_retriever.search(
            query=query_text,
            n_results=search_n_results,
            city=parsed.objective.get("city"),
            district=parsed.objective.get("district"),
            category=parsed.objective.get("sub_category"),
        )

        # RDB 필터(is_indoor/is_outdoor/has_parking/pet_size/시간 등)로 좁힌 후보에만 제한
        if has_candidates:
            candidate_set = set(candidate_ids)
            filtered = [r for r in results if r.get("content_id") in candidate_set]
            logger.info(
                "[PlaceService] ChromaDB candidate filter: %d -> %d (candidate_ids=%d)",
                len(results),
                len(filtered),
                len(candidate_ids),
            )
            results = filtered

        return results
    except Exception as e:
        logger.warning(f"[PlaceService] ChromaDB search failed: {e}")
        return []


async def _fetch_and_score(
    vector_results: list[dict],
    parsed: ParsedQuery,
    db: AsyncSession,
    n_results: int,
) -> list[dict]:
    """Join vector results with RDB details and calculate final scores."""
    if not vector_results:
        return []

    content_ids = [vr["content_id"] for vr in vector_results if vr.get("content_id")]
    if not content_ids:
        return []

    stmt = select(PlaceModel).where(PlaceModel.content_id.in_(content_ids))
    result = await db.execute(stmt)
    db_places = {p.content_id: p for p in result.scalars().all()}

    places = []
    for vr in vector_results:
        cid = vr.get("content_id", "")
        if cid not in db_places:
            continue
        if not _matches_fee_preferences(vr, parsed):
            continue

        place_dict = _to_dict(db_places[cid])
        rag_score = vr.get("similarity", 0.0)
        rule_score = _calc_rule_score(db_places[cid])
        category_bias = _calc_category_bias(db_places[cid], parsed)
        place_dict["similarity"] = rag_score
        place_dict["rag_score"] = rag_score
        place_dict["rule_score"] = rule_score
        place_dict["category_bias"] = category_bias
        place_dict["entrance_fee"] = vr.get("entrance_fee", "")
        place_dict["extra_fee"] = vr.get("extra_fee", "")
        place_dict["final_score"] = round(
            rag_score * 0.7 + rule_score * 0.3 + category_bias,
            4,
        )
        places.append(place_dict)

    prioritized = _apply_outing_priority(places, parsed, n_results)
    fee_filtered = _apply_fee_hard_filter(prioritized, parsed, source="vector")
    return _apply_restriction_hard_filter(fee_filtered, parsed, source="vector")


async def _fallback_rdb_only(
    parsed: ParsedQuery,
    candidate_ids: list[str],
    db: AsyncSession,
    n_results: int,
) -> list[dict]:
    """Build final results from RDB candidates only."""
    if not candidate_ids:
        logger.info("[PlaceService] fallback: no candidates, return empty list")
        return []

    stmt = select(PlaceModel).where(PlaceModel.content_id.in_(candidate_ids))
    result = await db.execute(stmt)
    places = result.scalars().all()

    scored = []
    for p in places:
        d = _to_dict(p)
        d["rule_score"] = _calc_rule_score(p)
        d["category_bias"] = _calc_category_bias(p, parsed)
        d["final_score"] = round(d["rule_score"] + d["category_bias"], 4)
        scored.append(d)

    prioritized = _apply_outing_priority(scored, parsed, n_results)
    fee_filtered = _apply_fee_hard_filter(prioritized, parsed, source="fallback")
    return _apply_restriction_hard_filter(fee_filtered, parsed, source="fallback")


async def _filter_with_relaxation(
    parsed: ParsedQuery,
    db: AsyncSession,
    max_candidates: int = 200,
) -> tuple[list[str], ParsedQuery]:
    """Relax strict objective filters step by step when no candidates are found."""
    candidate_ids = await _filter_by_rdb(parsed, db, max_candidates=max_candidates)
    if candidate_ids:
        return candidate_ids, parsed

    attempts: list[tuple[str, ParsedQuery]] = []

    if getattr(parsed, "landmark_coords", None):
        relaxed = _clone_parsed(parsed)
        relaxed.landmark = None
        relaxed.landmark_coords = None
        attempts.append(("landmark", relaxed))

    if parsed.objective.get("district"):
        relaxed = _clone_parsed(parsed)
        relaxed.objective["district"] = None
        attempts.append(("district", relaxed))

    if parsed.objective.get("district") and getattr(parsed, "landmark_coords", None):
        relaxed = _clone_parsed(parsed)
        relaxed.objective["district"] = None
        relaxed.landmark = None
        relaxed.landmark_coords = None
        attempts.append(("district+landmark", relaxed))

    if parsed.objective.get("sub_category") and parsed.objective.get("district"):
        relaxed = _clone_parsed(parsed)
        relaxed.objective["district"] = None
        relaxed.landmark = None
        relaxed.landmark_coords = None
        attempts.append(("sub_category+district+landmark", relaxed))

    if parsed.objective.get("sub_category"):
        relaxed = _clone_parsed(parsed)
        relaxed.objective["sub_category"] = None
        relaxed.landmark = None
        relaxed.landmark_coords = None
        attempts.append(("sub_category+landmark", relaxed))

    seen: set[tuple] = set()
    for label, relaxed in attempts:
        key = (
            relaxed.objective.get("city"),
            relaxed.objective.get("district"),
            relaxed.objective.get("sub_category"),
            relaxed.objective.get("is_indoor"),
            relaxed.objective.get("is_outdoor"),
            relaxed.landmark,
            relaxed.landmark_coords,
        )
        if key in seen:
            continue
        seen.add(key)

        candidate_ids = await _filter_by_rdb(relaxed, db, max_candidates=max_candidates)
        if candidate_ids:
            logger.info(
                f"[PlaceService] relaxation success: {label} -> {len(candidate_ids)} candidates"
            )
            return candidate_ids, relaxed

    return [], parsed


FACILITY_VECTOR_MIN_SIMILARITY = 0.45
SEOUL_ALIASES = {"서울", "서울특별시"}


@dataclass
class FacilitySearchResult:
    """시설정보 검색 결과 분기를 명시화한 dataclass.

    호출자(`_handle_facility`)가 못 찾음/서울 외 지역을 별도 안내 문구로
    구분하기 위해 두 분기를 동시에 표현한다.

    Attributes:
        facility: 매칭된 시설 dict (`_to_dict` + `match_source` + `match_confidence`).
                  미매칭 시 None.
        out_of_service_area: 발화에 명시된 도시가 서울이 아니어서 차단된 경우 True.
    """

    facility: dict | None = None
    out_of_service_area: bool = False


async def search_facility_by_name(
    query: str,
    db: AsyncSession,
    request: Request | None = None,
) -> FacilitySearchResult:
    """시설정보 의도 전용 단일 시설 검색.

    장소추천 파서(`_parse_query_with_llm` / `QueryParser`)는 객관(필터)·주관
    (분위기) 분리에 최적화돼 있어 시설명 추출에 부적합하다. 본 함수는
    `FacilityQueryParser` 로 시설명·도시 두 슬롯만 추출한 뒤:

        1) `Place.name LIKE %facility_name%` 정확 매칭 (서울 한정).
        2) 미스 시 ChromaDB 의미 유사도 top-3 → 첫 번째.
           유사도가 `FACILITY_VECTOR_MIN_SIMILARITY` 미만이면 신뢰 부족으로 미매칭.

    Args:
        query  : 사용자 발화 원문.
        db     : AsyncSession.
        request: FastAPI Request (AIContainer 접근용).

    Returns:
        FacilitySearchResult.
            - facility=dict, out_of_service_area=False : 매칭 성공.
            - facility=None, out_of_service_area=False : 못 찾음.
            - facility=None, out_of_service_area=True  : 서울 외 지역.
    """
    container = request.app.state.ai_container if request else None
    if container is None or not hasattr(container, "_facility_query_parser"):
        logger.info("[FacilityService] FacilityQueryParser 미주입 — 미매칭 처리")
        return FacilitySearchResult()

    parsed = await container._facility_query_parser.parse(query)
    facility_name = (parsed.get("facility_name") or "").strip()
    city = (parsed.get("city") or "").strip()

    if city and city not in SEOUL_ALIASES:
        logger.info(f"[FacilityService] out-of-service area: {city}")
        return FacilitySearchResult(out_of_service_area=True)

    if facility_name:
        stmt = (
            select(PlaceModel)
            .where(
                and_(
                    PlaceModel.name.like(f"%{facility_name}%"),
                    PlaceModel.address.like(f"%{SEOUL}%"),
                )
            )
            .order_by(func.length(PlaceModel.name).asc())
            .limit(3)
        )
        result = await db.execute(stmt)
        rows = result.scalars().all()
        if rows:
            place = rows[0]
            payload = _to_dict(place)
            payload["match_source"] = "name_exact"
            payload["match_confidence"] = 1.0 if len(rows) == 1 else 0.8
            payload["matched_keyword"] = facility_name
            logger.info(
                f"[FacilityService] name match '{facility_name}' -> {place.name} "
                f"(candidates={len(rows)})"
            )
            return FacilitySearchResult(facility=payload)

    try:
        vector_results = container._places_retriever.search(
            query=query,
            n_results=3,
            city=SEOUL,
        )
    except Exception as e:
        logger.warning(f"[FacilityService] ChromaDB search failed: {e}")
        return FacilitySearchResult()

    if not vector_results:
        return FacilitySearchResult()

    top = vector_results[0]
    similarity = float(top.get("similarity", 0.0) or 0.0)
    if similarity < FACILITY_VECTOR_MIN_SIMILARITY:
        logger.info(
            f"[FacilityService] top similarity {similarity:.3f} "
            f"< {FACILITY_VECTOR_MIN_SIMILARITY} -> 미매칭"
        )
        return FacilitySearchResult()

    cid = top.get("content_id")
    if not cid:
        return FacilitySearchResult()

    stmt = select(PlaceModel).where(PlaceModel.content_id == cid)
    result = await db.execute(stmt)
    place = result.scalar_one_or_none()
    if place is None:
        return FacilitySearchResult()

    payload = _to_dict(place)
    payload["match_source"] = "vector"
    payload["match_confidence"] = round(similarity, 4)
    payload["matched_keyword"] = None
    logger.info(
        f"[FacilityService] vector match -> {place.name} (sim={similarity:.3f})"
    )
    return FacilitySearchResult(facility=payload)


async def search_places_from_db(
    query: str,
    db: AsyncSession,
    n_results: int = 5,
    category: str = None,
    city: str = None,
    request: Request = None,
) -> list[dict]:
    """Run the hybrid place-search pipeline."""
    try:
        parsed = await _parse_query_with_llm(query, request)

        if _should_prioritize_outing(parsed):
            logger.info("[PlaceService] broad outing query detected, apply outing-first ranking")

        if city:
            parsed.objective["city"] = city
        if category:
            parsed.objective["sub_category"] = category

        requested_city = (parsed.objective.get("city") or "").strip()
        if requested_city and requested_city != SEOUL:
            logger.info(
                f"[PlaceService] out-of-service area requested: {requested_city} -> return empty result"
            )
            return []

        # LLM이 도시 파싱에 실패했더라도 쿼리에 서울 외 지역 키워드가 있으면 거부
        if not requested_city or requested_city == SEOUL:
            if any(kw in query for kw in OUT_OF_SERVICE_KEYWORDS):
                logger.info(
                    f"[PlaceService] keyword-based out-of-service detected: {query} -> return empty result"
                )
                return []

        if parsed.landmark:
            parsed.landmark_coords = await _get_landmark_coords(parsed.landmark)

        candidate_ids, parsed = await _filter_with_relaxation(parsed, db, max_candidates=200)

        if parsed.time_condition:
            candidate_ids = await _filter_by_time(candidate_ids, parsed.time_condition, db)

        if not (parsed.subjective or "").strip() and not _has_fee_preferences(parsed):
            logger.info("[PlaceService] subjective empty, use RDB fallback first")
            return await _fallback_rdb_only(parsed, candidate_ids, db, n_results)

        vector_results = await _search_by_chromadb(
            parsed, candidate_ids, n_results, request
        )

        if vector_results:
            places = await _fetch_and_score(vector_results, parsed, db, n_results)
            if places:
                return places[:n_results]

        if _has_fee_preferences(parsed):
            logger.info("[PlaceService] fee preferences requested but no matching metadata found")
            return []

        logger.info("[PlaceService] ChromaDB returned no result, use RDB fallback")
        return await _fallback_rdb_only(parsed, candidate_ids, db, n_results)

    except Exception as e:
        logger.error(f"[PlaceService] place search failed: {e}")
        return []

def _calc_rule_score(place: PlaceModel) -> float:
    """Calculate a simple rule-based dog-friendliness score."""
    score = 0.0
    if place.pet_zone_type == FULL_ZONE:
        score += 0.4
    if place.pet_restrictions in (None, "", NO_RESTRICTION):
        score += 0.3
    if place.is_outdoor:
        score += 0.2
    if place.has_parking and place.has_parking.value == "Y":
        score += 0.1
    return round(min(score, 1.0), 4)

def _to_dict(place: PlaceModel) -> dict:
    """Convert a PlaceModel instance into an API response dict."""
    restriction_tags = sorted(_extract_restriction_tags(place.pet_restrictions))
    return {
        "name": place.name or "",
        "address": place.address or "",
        "category": _place_type.get_type(place.content_type_id),
        "sub_category": place.sub_category or "",
        "content_id": place.content_id or "",
        "lat": float(place.latitude) if place.latitude else 0.0,
        "lng": float(place.longitude) if place.longitude else 0.0,
        "tel": place.tel or "",
        "conditions": place.pet_restrictions or "",
        "restriction_tags": restriction_tags,
        "pet_zone": place.pet_zone_type or "",
        "pet_size": place.pet_size_limit or "",
        "has_parking": place.has_parking.value if place.has_parking else "",
        "operation": place.operation_info or "",
        "indoor": "Y" if place.is_indoor else "N",
        "outdoor": "Y" if place.is_outdoor else "N",
        "description": place.description or "",
        "entrance_fee": "",
        "extra_fee": "",
        "entrance_fee_amount": place.entrance_fee_amount,
        "entrance_fee_type":   place.entrance_fee_type.value if place.entrance_fee_type else "unknown",
        "extra_fee_amount":    place.extra_fee_amount,
        "extra_fee_type":      place.extra_fee_type.value if place.extra_fee_type else "unknown",
        "similarity": 0.0,
        "rag_score": 0.0,
        "rule_score": 0.0,
        "final_score": 0.0,
    }
