import re
import httpx
import logging
import math

from copy import deepcopy
from fastapi import Request
from dataclasses import dataclass
from core.config import settings
from core.type.place import PlaceType
from models.place import Place as PlaceModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, case, func, not_, or_, select

logger = logging.getLogger(__name__)

_place_type = PlaceType()

'''
- 외부 API / 랜드마크 반경 설정
    "...근처" 같은 쿼리에서 랜드마크 좌표를 카카오 API로 변환할 때 사용.
    장소 후보가 3개 미만이면 다시 1km → 2km → 3km 순으로 자동 확장합니다.
'''
KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"
LANDMARK_RADIUS_STEPS_M = (1000, 2000, 3000) # 랜드마크 반경 확장 단계
LANDMARK_MIN_RESULTS = 3                     # 장소 후보 최소 3개

# Ablation A: RDB 후보와 Chroma 후보 풀을 넓혀 RDB 후보 제한으로 좋은 벡터 후보가
# 잘리는지 확인한다. 기존 기준값은 각각 200, 50이었다.
RDB_FILTER_MAX_CANDIDATES = 500
CHROMA_FILTERED_FETCH_N = 200


SEOUL = "서울특별시" # 현재 서비스가 서울만 제공하기 때문에 만든 필터 상수

'''
- 운영시간 파싱용 문자열 상수
    DB에 저장된 운영시간(operation_info 칼럼) 텍스트를
    파싱할 때(_parse_operation_hours) 문자열 비교에 사용.
    LLM이 time_condition으로 뽑아주는 값도 이 상수들과 매핑됩니다.
'''
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

'''
- 카테고리 분류 상수
'''
FULL_ZONE = "전구역"
NO_RESTRICTION = "제한사항 없음"
OUTING_SUBCATEGORIES = {"공원", "관광지", "반려견놀이터", "카페", "식당"} # 광범위 추천 쿼리일 때 우선 노출
DEFAULT_RECOMMENDABLE_SUBCATEGORIES = {
    "공원",
    "관광지",
    "레포츠",
    "문예회관",
    "문화시설",
    "미술관",
    "박물관",
    "반려견놀이터",
    "숙박",
    "식당",
    "카페",
    "펜션",
    "호텔",
}
PURPOSE_ONLY_SUBCATEGORIES = {"동물병원", "동물약국", "반려동물용품", "미용", "위탁관리"}
DEPRIORITIZED_SUBCATEGORIES = PURPOSE_ONLY_SUBCATEGORIES # 목적형 질문이 아니면 기본 추천에서 제외
# 쿼리에 이 단어가 있으면 "구체적 목적 있는 질문"으로 판단; 카테고리 우선순위 조정 안 함
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
'''
- 장소 유형 별칭 / 크기 판단 / 서비스 외 지역
'''
# "산책할 곳 추천"처럼 장소 유형이 명시 안 된 광범위 질문 감지용
GENERIC_PLACE_TARGETS = {
    "곳",
    "장소",
    "코스",
    "나들이",
    "외출",
    "산책",
    "데이트",
    "스팟",
}
PLACE_TYPE_ALIASES = {
    "놀이터": {"놀이터", "반려견놀이터"},
    "강아지놀이터": {"강아지놀이터", "반려견놀이터"},
    "애견놀이터": {"애견놀이터", "반려견놀이터"},
    "식물원": {"식물원", "수목원"},
    "수목원": {"수목원", "식물원"},
    "숙소": {"숙소", "숙박", "호텔", "펜션"},
    "숙박": {"숙소", "숙박", "호텔", "펜션"},
    "강아지호텔": {"강아지호텔", "애견호텔", "펫호텔", "위탁관리"},
    "애견호텔": {"강아지호텔", "애견호텔", "펫호텔", "위탁관리"},
    "펫호텔": {"강아지호텔", "애견호텔", "펫호텔", "위탁관리"},
    "동물병원": {"동물병원", "병원"},
    "병원": {"동물병원", "병원"},
    "동물약국": {"동물약국", "약국"},
    "약국": {"동물약국", "약국"},
    "용품점": {"용품점", "용품", "반려동물용품"},
    "용품": {"용품점", "용품", "반려동물용품"},
    "문화시설": {"문화시설", "문예회관", "미술관", "박물관"},
}

SUB_CATEGORY_GROUPS = {
    "문화시설": {"문화시설", "문예회관", "미술관", "박물관"},
    "문예회관": {"문화시설", "문예회관", "미술관", "박물관"},
    "미술관": {"문화시설", "문예회관", "미술관", "박물관"},
    "박물관": {"문화시설", "문예회관", "미술관", "박물관"},
    "숙박": {"숙박", "펜션", "호텔"},
    "펜션": {"숙박", "펜션", "호텔"},
    "호텔": {"숙박", "펜션", "호텔"},
    "강아지호텔": {"위탁관리"},
    "애견호텔": {"위탁관리"},
    "펫호텔": {"위탁관리"},
}

# "소형 카페" vs "소형견" 처럼 크기 단어의 대상이 장소인지 동물인지 구분
PET_SIZE_CONTEXT_WORDS = ("반려견", "강아지", "개", "아이", "댕댕이", "견")
PLACE_SIZE_CONTEXT_WORDS = ("카페", "식당", "공원", "숙소", "호텔", "펜션", "놀이터", "공간", "매장")
# 서울 외 지역 요청이면 검색 자체를 차단하고 안내 메시지 반환 (현재 서비스 상태; 서울 지역만.)
OUT_OF_SERVICE_KEYWORDS = (
    "제주", "부산", "강원", "경주", "속초", "동해", "인천", "수원", "대전",
    "가평", "경기", "충청", "전라", "경상", "울산", "광주", "대구", "세종",
    "춘천", "강릉", "여수", "통영", "거제", "포항", "안동", "전주", "청주",
    "해운대", "제주도", "고양", "성남", "용인", "평택", "화성",
)


class ParsedQuery:
    """장소 검색 쿼리 조건을 담는 컨테이너."""

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
        self.use_current_location: bool = False
        self.landmark: str | None = None
        self.landmark_coords: tuple[float, float] | None = None


def _extract_restriction_tags(text: str | None) -> set[str]:
    """반려동물 제한사항 자유형식 텍스트를 태그 집합으로 정규화."""
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
    """쿼리 의도에서 제한사항 선호 조건(허용/금지 태그)을 해석해 반환."""
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
    """제한사항이 핵심 의도인 쿼리에서 과잉 필터 조건을 완화."""
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
    """크기 단어가 반려견 크기인지 장소 크기인지 판단해 objective/subjective에 반영."""
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
    """요금 관련 표현을 구조화된 선호 조건(entrance_fee_preference 등)으로 변환."""
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
    """용품 관련 표현을 구조화된 선호 조건(waste_bag_preference 등)으로 변환."""
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
    """결과 반환 전 요금 조건을 기준으로 최종 하드 필터링 적용."""
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
    """정규화된 제한사항 태그를 기준으로 최종 하드 필터링 적용."""
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
    """사용자 질문(query)을 객관적(objective)와 주관적(subjective)으로 파싱."""
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
            parsed.use_current_location = bool(result.get("use_current_location", False))
            parsed.landmark = result.get("landmark")
            _normalize_sub_category_intent(parsed)
            _normalize_size_interpretation(parsed)
    except Exception as e:
        logger.warning(f"[PlaceService] LLM query parsing failed, using defaults: {e}")

    _normalize_sub_category_intent(parsed)
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
    cloned.use_current_location = getattr(parsed, "use_current_location", False)
    cloned.landmark = getattr(parsed, "landmark", None)
    cloned.landmark_coords = getattr(parsed, "landmark_coords", None)
    return cloned


def _has_explicit_place_purpose(query: str) -> bool:
    """쿼리에 구체적인 장소 유형이 명시된 경우 True 반환."""
    return any(keyword in (query or "") for keyword in EXPLICIT_PURPOSE_KEYWORDS)


def _extract_requested_place_type(query: str) -> str | None:
    """추천 문구에서 사용자가 명시한 장소 유형 텍스트 추출."""
    text = (query or "").strip()
    if not text:
        return None

    patterns = (
        r"(?:가능한|되는|갈\s*수\s*있는|이용\s*가능한|동반\s*가능한)\s+([가-힣A-Za-z0-9]+)\s*(?:추천|알려|찾아)",
        r"([가-힣A-Za-z0-9]+)\s*(?:추천|알려|찾아)\s*(?:해줘|줘|주세요)?$",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        target = match.group(1).strip()
        target = re.sub(r"(은|는|이|가|을|를|도|만|좀)$", "", target)
        if target and target not in GENERIC_PLACE_TARGETS:
            return target

    return None


def _expand_place_type_aliases(place_type: str) -> set[str]:
    return {place_type, *PLACE_TYPE_ALIASES.get(place_type, set())}


def _expand_sub_categories(sub_category: str | None) -> set[str]:
    if not sub_category:
        return set()
    return {sub_category, *SUB_CATEGORY_GROUPS.get(sub_category, set())}


def _normalize_sub_category_intent(parsed: ParsedQuery) -> None:
    query = (parsed.raw_query or "").replace(" ", "")
    if not query:
        return

    pet_hotel_keywords = ("강아지호텔", "애견호텔", "펫호텔", "펫시터", "데이케어")
    if any(keyword in query for keyword in pet_hotel_keywords):
        parsed.objective["sub_category"] = "위탁관리"
        return

    if "문화시설" in query:
        parsed.objective["sub_category"] = "문화시설"
        return

    if "문예회관" in query:
        parsed.objective["sub_category"] = "문예회관"


def _requires_requested_place_type_filter(query: str, parsed: ParsedQuery) -> bool:
    if parsed.objective.get("sub_category"):
        return False

    requested = _extract_requested_place_type(query)
    if not requested:
        return False

    terms = _expand_place_type_aliases(requested)
    return not bool(terms.intersection(EXPLICIT_PURPOSE_KEYWORDS))


async def _is_unsupported_requested_place_type(
    query: str,
    parsed: ParsedQuery,
    db: AsyncSession,
) -> bool:
    """사용자가 요청한 장소 유형이 DB에 존재하지 않으면 True 반환."""
    if parsed.objective.get("sub_category"):
        return False

    requested = _extract_requested_place_type(query)
    if not requested:
        return False

    candidates = _expand_place_type_aliases(requested)
    if candidates.intersection(EXPLICIT_PURPOSE_KEYWORDS):
        return False

    try:
        text_conditions = []
        for candidate in candidates:
            text_conditions.extend(
                [
                    PlaceModel.name.like(f"%{candidate}%"),
                    PlaceModel.sub_category.like(f"%{candidate}%"),
                    PlaceModel.description.like(f"%{candidate}%"),
                ]
            )
        existing_stmt = (
            select(PlaceModel.content_id)
            .where(or_(*text_conditions))
            .limit(1)
        )
        existing = await db.execute(existing_stmt)
        if existing.first():
            return False

        result = await db.execute(select(PlaceModel.sub_category).distinct())
        supported = {row[0] for row in result.fetchall() if row[0]}
    except Exception as e:
        logger.warning(f"[PlaceService] supported category lookup failed: {e}")
        return False

    supported.update(EXPLICIT_PURPOSE_KEYWORDS)
    supported.update(_place_type.types.values())
    return not candidates.intersection(supported)


async def _filter_candidate_ids_by_requested_place_type(
    candidate_ids: list[str],
    query: str,
    parsed: ParsedQuery,
    db: AsyncSession,
) -> list[str]:
    """DB 텍스트에서 사용자가 명시한 장소 유형과 일치하는 후보만 유지."""
    if not candidate_ids or not _requires_requested_place_type_filter(query, parsed):
        return candidate_ids

    requested = _extract_requested_place_type(query)
    terms = _expand_place_type_aliases(requested)

    text_conditions = []
    for term in terms:
        text_conditions.extend(
            [
                PlaceModel.name.like(f"%{term}%"),
                PlaceModel.sub_category.like(f"%{term}%"),
                PlaceModel.description.like(f"%{term}%"),
            ]
        )

    stmt = (
        select(PlaceModel.content_id)
        .where(
            and_(
                PlaceModel.content_id.in_(candidate_ids),
                or_(*text_conditions),
            )
        )
    )
    result = await db.execute(stmt)
    filtered_ids = [row[0] for row in result.fetchall()]
    logger.info(
        "[PlaceService] requested place type filter (%s): %d -> %d",
        requested,
        len(candidate_ids),
        len(filtered_ids),
    )
    if len(filtered_ids) < min(5, len(candidate_ids)):
        logger.info(
            "[PlaceService] requested place type filter relaxed (%s): keep original candidates",
            requested,
        )
        return candidate_ids

    return filtered_ids


def _should_prioritize_outing(parsed: ParsedQuery) -> bool:
    """광범위 추천 질문일 때만 나들이 카테고리 우선 정렬을 적용."""
    return (
        not parsed.objective.get("sub_category")
        and not _has_explicit_place_purpose(parsed.raw_query)
    )


def _allows_purpose_only_categories(parsed: ParsedQuery) -> bool:
    """병원/약국/용품/미용/위탁관리처럼 목적형 카테고리를 허용할지 판단."""
    sub_categories = _expand_sub_categories(parsed.objective.get("sub_category"))
    if sub_categories.intersection(PURPOSE_ONLY_SUBCATEGORIES):
        return True

    purpose_keywords = {
        "병원",
        "동물병원",
        "약국",
        "동물약국",
        "펫샵",
        "팻샵",
        "용품",
        "용품점",
        "반려동물용품",
        "미용",
        "그루밍",
        "위탁",
        "펫시터",
        "강아지호텔",
        "애견호텔",
        "펫호텔",
        "데이케어",
    }
    query = parsed.raw_query or ""
    return any(keyword in query for keyword in purpose_keywords)


def _allowed_result_subcategories(parsed: ParsedQuery) -> set[str] | None:
    """현재 쿼리에서 최종 결과로 허용되는 sub_category 집합."""
    sub_category = parsed.objective.get("sub_category")
    if sub_category:
        return _expand_sub_categories(sub_category)
    if _allows_purpose_only_categories(parsed):
        return PURPOSE_ONLY_SUBCATEGORIES
    return DEFAULT_RECOMMENDABLE_SUBCATEGORIES


def _apply_category_guard(
    places: list[dict],
    parsed: ParsedQuery,
    *,
    source: str,
) -> list[dict]:
    """목적형 카테고리가 일반 장소 추천 결과에 섞이지 않도록 최종 방어."""
    allowed = _allowed_result_subcategories(parsed)
    if allowed is None:
        return places

    kept = [
        place
        for place in places
        if (place.get("sub_category") or "").strip() in allowed
    ]
    if len(kept) != len(places):
        logger.info(
            "[PlaceService] category guard (%s): %d -> %d (allowed=%s)",
            source,
            len(places),
            len(kept),
            sorted(allowed),
        )
    return kept


def _calc_category_bias(place: PlaceModel, parsed: ParsedQuery) -> float:
    """광범위 질문에서 나들이 친화 카테고리에 소폭의 랭킹 보정값 계산."""
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


def _tokenize_query_for_relevance(parsed: ParsedQuery) -> list[str]:
    """Extract lightweight query tokens for RDB fallback tie-breaking."""
    stopwords = {
        "서울",
        "서울특별시",
        "추천",
        "장소",
        "근처",
        "주변",
        "가능",
        "가능한",
        "반려견",
        "강아지",
        "애견",
        "동반",
        "곳",
        "있는",
        "없는",
        "해줘",
        "해주세요",
    }
    sources = [
        parsed.raw_query or "",
        parsed.subjective or "",
        parsed.objective.get("city") or "",
        parsed.objective.get("district") or "",
        parsed.objective.get("sub_category") or "",
        parsed.landmark or "",
    ]
    tokens: list[str] = []
    seen: set[str] = set()
    for source in sources:
        for token in re.findall(r"[가-힣A-Za-z0-9]+", str(source)):
            token = token.strip()
            if len(token) < 2 or token in stopwords or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tokens


def _contains_token(text: str | None, token: str) -> bool:
    if not text or not token:
        return False
    compact_text = re.sub(r"\s+", "", str(text)).lower()
    compact_token = re.sub(r"\s+", "", str(token)).lower()
    return compact_token in compact_text


def _calc_query_relevance_bonus(place: PlaceModel, parsed: ParsedQuery) -> float:
    """Small RDB fallback bonus for direct query-field relevance.

    This is intentionally lightweight. ChromaDB remains the main semantic
    signal; this bonus only breaks ties among RDB fallback candidates.
    """
    bonus = 0.0
    sub_category = (place.sub_category or "").strip()
    requested_sub_category = (parsed.objective.get("sub_category") or "").strip()

    if requested_sub_category:
        expanded = _expand_sub_categories(requested_sub_category)
        if sub_category == requested_sub_category:
            bonus += 0.10
        elif sub_category in expanded:
            bonus += 0.04

    district = (parsed.objective.get("district") or "").strip()
    if district and _contains_token(place.address, district):
        bonus += 0.05

    landmark = (parsed.landmark or "").strip()
    if landmark and (
        _contains_token(place.name, landmark)
        or _contains_token(place.address, landmark)
        or _contains_token(place.description, landmark)
    ):
        bonus += 0.04

    name_hits = 0
    sub_category_hits = 0
    address_hits = 0
    description_hits = 0
    subjective_tokens = _tokenize_query_for_relevance(
        ParsedQuery(parsed.subjective or "")
    ) if parsed.subjective else []
    query_tokens = _tokenize_query_for_relevance(parsed)

    for token in query_tokens:
        if _contains_token(place.name, token):
            name_hits += 1
        if _contains_token(sub_category, token):
            sub_category_hits += 1
        if _contains_token(place.address, token):
            address_hits += 1
        if _contains_token(place.description, token):
            description_hits += 1

    subjective_description_hits = sum(
        1 for token in subjective_tokens if _contains_token(place.description, token)
    )

    bonus += min(name_hits * 0.04, 0.08)
    bonus += min(sub_category_hits * 0.03, 0.06)
    bonus += min(address_hits * 0.02, 0.04)
    bonus += min(description_hits * 0.015, 0.06)
    bonus += min(subjective_description_hits * 0.02, 0.08)

    return round(min(bonus, 0.25), 4)


def _distance_meters(
    lat1: float | None,
    lng1: float | None,
    lat2: float | None,
    lng2: float | None,
) -> float | None:
    if None in (lat1, lng1, lat2, lng2):
        return None
    try:
        lat1_f, lng1_f = float(lat1), float(lng1)
        lat2_f, lng2_f = float(lat2), float(lng2)
    except (TypeError, ValueError):
        return None

    radius_m = 6371000
    phi1 = math.radians(lat1_f)
    phi2 = math.radians(lat2_f)
    d_phi = math.radians(lat2_f - lat1_f)
    d_lam = math.radians(lng2_f - lng1_f)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lam / 2) ** 2
    )
    return radius_m * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _calc_distance_bonus(place: PlaceModel, parsed: ParsedQuery) -> float:
    if not parsed.landmark_coords:
        return 0.0
    lat, lng = parsed.landmark_coords
    distance = _distance_meters(lat, lng, place.latitude, place.longitude)
    if distance is None:
        return 0.0
    if distance <= 1000:
        return 0.08
    if distance <= 2000:
        return 0.05
    if distance <= 3000:
        return 0.03
    return 0.0


def _calc_category_match_bonus(place: PlaceModel, parsed: ParsedQuery) -> float:
    requested = (parsed.objective.get("sub_category") or "").strip()
    if not requested:
        return 0.0
    sub_category = (place.sub_category or "").strip()
    if sub_category == requested:
        return 0.05
    if sub_category in _expand_sub_categories(requested):
        return 0.02
    return 0.0


def _calc_time_match_bonus(place: PlaceModel, parsed: ParsedQuery) -> float:
    time_condition = parsed.time_condition
    if not time_condition or not place.operation_info or NO_INFO in place.operation_info:
        return 0.0
    hours = _parse_operation_hours(place.operation_info)
    if not hours:
        return 0.0

    earliest = hours.get("earliest_open", 2400)
    latest = hours.get("latest_close", 0)

    if time_condition == OPEN_24H and hours.get("is_24hours", False):
        return 0.06
    if time_condition == ALWAYS_OPEN and hours.get("always_open", False):
        return 0.05
    if time_condition == WEEKEND and hours.get("has_weekend", False):
        return 0.04
    if time_condition == EARLY_MORNING and earliest <= 800:
        return 0.04
    if time_condition == MORNING and earliest <= 900:
        return 0.03
    if time_condition == LUNCH and earliest <= 1100 and latest >= 1500:
        return 0.03
    if time_condition == EVENING and latest >= 1900:
        return 0.03
    if time_condition == NIGHT and latest >= 2200:
        return 0.04
    return 0.0


def _calc_condition_match_bonus(place: PlaceModel, parsed: ParsedQuery) -> float:
    """Small explicit-condition bonus for RDB fallback tie-breaking."""
    bonus = (
        _calc_distance_bonus(place, parsed)
        + _calc_category_match_bonus(place, parsed)
        + _calc_time_match_bonus(place, parsed)
    )
    return round(min(bonus, 0.15), 4)


def _apply_outing_priority(
    places: list[dict],
    parsed: ParsedQuery,
    n_results: int,
) -> list[dict]:
    """광범위 추천 쿼리에서 나들이 친화 카테고리를 결과 상위로 배치."""
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
    """카카오 키워드 검색으로 랜드마크 위경도 좌표 조회."""
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
    """objective 조건으로 RDB에서 후보 content_id 목록 필터링."""
    obj = parsed.objective
    conditions = []

    if obj.get("city"):
        conditions.append(PlaceModel.address.like(f"%{obj['city']}%"))
    if obj.get("district"):
        conditions.append(PlaceModel.address.like(f"%{obj['district']}%"))
    if obj.get("sub_category"):
        sub_categories = _expand_sub_categories(obj["sub_category"])
        conditions.append(PlaceModel.sub_category.in_(sub_categories))
    elif _allows_purpose_only_categories(parsed):
        conditions.append(PlaceModel.sub_category.in_(PURPOSE_ONLY_SUBCATEGORIES))
    elif not _allows_purpose_only_categories(parsed):
        conditions.append(PlaceModel.sub_category.in_(DEFAULT_RECOMMENDABLE_SUBCATEGORIES))
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
        order_by = []
        if parsed.landmark_coords:
            lat, lng = parsed.landmark_coords
            distance_expr = func.ST_Distance_Sphere(
                func.point(PlaceModel.longitude, PlaceModel.latitude),
                func.point(lng, lat),
            )
            order_by.append(distance_expr.asc())
        else:
            order_by.extend(
                [
                    case((PlaceModel.pet_zone_type == FULL_ZONE, 1), else_=0).desc(),
                    case(
                        (
                            or_(
                                PlaceModel.pet_restrictions.is_(None),
                                PlaceModel.pet_restrictions == "",
                                PlaceModel.pet_restrictions == NO_RESTRICTION,
                            ),
                            1,
                        ),
                        else_=0,
                    ).desc(),
                    case((PlaceModel.has_parking == "Y", 1), else_=0).desc(),
                    case((PlaceModel.is_indoor.is_(True), 1), else_=0).desc(),
                    case((PlaceModel.is_outdoor.is_(True), 1), else_=0).desc(),
                ]
            )
        order_by.append(PlaceModel.content_id.asc())
        stmt = (
            select(PlaceModel.content_id)
            .where(and_(*all_conditions) if all_conditions else True)
            .order_by(*order_by)
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
    """operation_info 텍스트를 비교 가능한 운영시간·휴무 dict로 파싱."""
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

    # 월~금 요일별 휴무 감지
    for day_char, key in [("월", "closed_on_mon"), ("화", "closed_on_tue"), ("수", "closed_on_wed"), ("목", "closed_on_thu"), ("금", "closed_on_fri")]:
        result[key] = day_char in closed_part and not result["always_open"]

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
    elif not result.get("is_24hours") and not result.get("always_open"):
        logger.warning(
            "[PlaceService] 운영시간 시간대 패턴 미인식 — DB 값 확인 필요 | operation_info=%.100s",
            operation_info,
        )

    if result["is_24hours"]:
        result["earliest_open"] = 0
        result["latest_close"] = 2400

    result["has_sat"] = "토" in hours_part
    result["has_sun"] = "일" in hours_part or DAILY in hours_part
    result["has_weekend"] = result["has_sat"] or result["has_sun"]

    return result


def _check_time_condition(operation_info: str | None, time_condition: str) -> bool:
    """장소가 요청된 시간 조건을 만족하면 True 반환."""
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
        return earliest <= 1100 and latest >= 1400
    if time_condition == EVENING:
        return latest >= 1700
    if time_condition == NIGHT:
        return latest >= 2100
    if time_condition == OPEN_24H:
        return h.get("is_24hours", False) or latest >= 2400
    if time_condition == ALWAYS_OPEN:
        return h.get("always_open", False)
    if time_condition == WEEKEND:
        return h.get("has_weekend", False)
    if time_condition == HOLIDAY:
        return not h.get("closed_on_holiday", True)

    return True


def _sort_by_time_certainty(places: list[dict], time_condition: str) -> list[dict]:
    """시간 조건 검색 시 운영시간 확인된 장소를 미확인 장소 앞으로 재정렬."""
    confirmed, uncertain = [], []
    for p in places:
        op_info = p.get("operation", "")
        if op_info and NO_INFO not in op_info and _parse_operation_hours(op_info):
            confirmed.append(p)
        else:
            uncertain.append(p)
    return confirmed + uncertain


async def _filter_by_time(
    candidate_ids: list[str],
    time_condition: str | None,
    db: AsyncSession,
) -> list[str]:
    """시간 조건으로 후보 ID를 필터링하며, 결과가 0건이면 원본 리스트 유지."""
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
    """쿼리의 주관적(subjective) 부분으로 ChromaDB 유사도 검색 실행."""
    try:
        container = request.app.state.ai_container if request else None
        if not container:
            return []

        query_text = (parsed.subjective or "").strip() or parsed.raw_query

        # candidate_ids가 있으면 후처리 필터를 위해 여유롭게 더 가져온다
        has_candidates = bool(candidate_ids)
        fetch_n = max(n_results, CHROMA_FILTERED_FETCH_N) if has_candidates else n_results
        search_n_results = max(fetch_n, 20) if _has_fee_preferences(parsed) else fetch_n

        sub_categories = _expand_sub_categories(parsed.objective.get("sub_category"))
        vector_category = parsed.objective.get("sub_category") if len(sub_categories) <= 1 else None

        results = container._places_retriever.search(
            query=query_text,
            n_results=search_n_results,
            city=parsed.objective.get("city"),
            district=parsed.objective.get("district"),
            category=vector_category,
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
    """벡터 검색 결과를 RDB 상세정보와 조인해 최종 점수(rag+rule+bias) 계산."""
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
            rag_score * 0.5 + rule_score * 0.5 + category_bias,
            4,
        )
        places.append(place_dict)

    category_filtered = _apply_category_guard(places, parsed, source="vector")
    prioritized = _apply_outing_priority(category_filtered, parsed, n_results)
    fee_filtered = _apply_fee_hard_filter(prioritized, parsed, source="vector")
    return _apply_restriction_hard_filter(fee_filtered, parsed, source="vector")


async def _fallback_rdb_only(
    parsed: ParsedQuery,
    candidate_ids: list[str],
    db: AsyncSession,
    n_results: int,
) -> list[dict]:
    """RDB 후보만으로 최종 결과 구성 (ChromaDB 미사용 폴백)."""
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
        d["query_relevance_bonus"] = _calc_query_relevance_bonus(p, parsed)
        d["condition_match_bonus"] = _calc_condition_match_bonus(p, parsed)
        d["final_score"] = round(
            d["rule_score"]
            + d["category_bias"]
            + d["query_relevance_bonus"]
            + d["condition_match_bonus"],
            4,
        )
        scored.append(d)

    category_filtered = _apply_category_guard(scored, parsed, source="fallback")
    prioritized = _apply_outing_priority(category_filtered, parsed, n_results)
    fee_filtered = _apply_fee_hard_filter(prioritized, parsed, source="fallback")
    return _apply_restriction_hard_filter(fee_filtered, parsed, source="fallback")


async def diagnose_rdb_retrieval(
    query: str,
    db: AsyncSession,
    request: Request = None,
    user_lat: float = None,
    user_lng: float = None,
    pre_parsed: dict | ParsedQuery | None = None,
) -> dict:
    """Return evaluation-only diagnostics for the RDB candidate/ranking path.

    This helper does not change production search behavior. It mirrors the
    RDB candidate path used by rdb_only/fallback so evaluation output can tell
    whether a miss came from parsing, candidate generation, or ranking.
    """
    try:
        if isinstance(pre_parsed, ParsedQuery):
            parsed = _clone_parsed(pre_parsed)
        elif pre_parsed:
            parsed = ParsedQuery(query)
            parsed.objective = deepcopy(pre_parsed["objective"])
            parsed.subjective = pre_parsed.get("subjective", query)
            parsed.time_condition = pre_parsed.get("time_condition")
            parsed.use_current_location = pre_parsed.get("use_current_location", False)
            parsed.landmark = pre_parsed.get("landmark")
            parsed.landmark_coords = pre_parsed.get("landmark_coords")
        else:
            parsed = await _parse_query_with_llm(query, request)

        if parsed.use_current_location:
            parsed.landmark = None
            if user_lat and user_lng:
                parsed.landmark_coords = (user_lat, user_lng)
        elif parsed.landmark:
            parsed.landmark_coords = await _get_landmark_coords(parsed.landmark)

        if not parsed.landmark_coords and user_lat and user_lng:
            parsed.landmark_coords = (user_lat, user_lng)

        candidate_ids, parsed = await _filter_with_relaxation(
            parsed,
            db,
            max_candidates=RDB_FILTER_MAX_CANDIDATES,
        )
        candidate_ids = await _filter_candidate_ids_by_requested_place_type(
            candidate_ids, query, parsed, db
        )
        if parsed.time_condition:
            candidate_ids = await _filter_by_time(candidate_ids, parsed.time_condition, db)

        candidate_names: list[str] = []
        if candidate_ids:
            stmt = select(PlaceModel).where(PlaceModel.content_id.in_(candidate_ids))
            result = await db.execute(stmt)
            places_by_id = {p.content_id: p for p in result.scalars().all()}
            candidate_names = [
                places_by_id[cid].name or ""
                for cid in candidate_ids
                if cid in places_by_id
            ]

        ranked = await _fallback_rdb_only(parsed, candidate_ids, db, len(candidate_ids))
        ranked_names = [p.get("name", "") for p in ranked if p.get("name")]

        return {
            "parsed_objective": parsed.objective,
            "parsed_subjective": parsed.subjective,
            "time_condition": parsed.time_condition,
            "use_current_location": parsed.use_current_location,
            "landmark": parsed.landmark,
            "landmark_coords": parsed.landmark_coords,
            "rdb_candidate_count": len(candidate_ids),
            "rdb_candidate_names": candidate_names,
            "rdb_ranked_names": ranked_names,
        }
    except Exception as e:
        logger.warning("[PlaceService] RDB diagnostic failed: %s", e)
        return {"diagnostic_error": str(e)}


async def _filter_with_relaxation(
    parsed: ParsedQuery,
    db: AsyncSession,
    max_candidates: int = 200,
) -> tuple[list[str], ParsedQuery]:
    """후보가 0건이면 objective 필터를 단계적으로 완화해 재시도."""
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

async def lookup_facility_by_name(
    name: str,
    db: AsyncSession,
) -> dict | None:
    """장소 이름 기반 단일 시설정보 조회.

    채팅 응답 카드에서 사용자가 장소 링크를 클릭했을 때, 카드에 표시된
    장소명(예: "더포트", "바잇미", "반포 한강공원")을 그대로 받아 시설
    상세를 반환한다. 카드의 `name` 은 `_to_dict` 가 `Place.name` 을
    그대로 직렬화한 값이므로 정확 매칭이 1차 전략이고, 시드 갱신·공백
    차이 등으로 정확 매칭이 미스인 케이스를 위해 LIKE fallback 을 둔다.
    서비스 지역인 서울 한정으로 검색하여 동명 시설이 다른 도시에 있을
    경우의 오매칭을 차단한다.

    LLM·ChromaDB 호출 없이 RDB 단건 조회만 수행 — hallucinate 0.

    Args:
        name: 장소명 원문 (URL 디코딩 후, 트림 전 상태도 허용).
        db  : AsyncSession.

    Returns:
        `FacilityCard` 직렬화 가능한 dict. 미존재 시 None.
        동명 시설이 다수일 경우 가장 짧은 name → id 오름차순 으로 결정적
        으로 1건 선택. 반환 dict 는 `match_source="name_exact"`,
        `match_confidence=1.0` 으로 고정되어 약한 매칭 경고 UI 가
        노출되지 않도록 한다.
    """
    cleaned = (name or "").strip()

    if not cleaned:
        return None

    seoul_filter = PlaceModel.address.like(f"%{SEOUL}%")
    base_order = (func.length(PlaceModel.name).asc(), PlaceModel.id.asc())

    exact_stmt = (
        select(PlaceModel)
        .where(and_(PlaceModel.name == cleaned, seoul_filter))
        .order_by(*base_order)
        .limit(1)
    )
    place = (await db.execute(exact_stmt)).scalar_one_or_none()

    if place is None:
        like_stmt = (
            select(PlaceModel)
            .where(and_(PlaceModel.name.like(f"%{cleaned}%"), seoul_filter))
            .order_by(*base_order)
            .limit(1)
        )
        place = (await db.execute(like_stmt)).scalar_one_or_none()

    if place is None:
        return None

    payload = _to_dict(place)
    payload["match_source"] = "name_exact"
    payload["match_confidence"] = 1.0

    return payload

async def search_places_from_db(
    query: str,
    db: AsyncSession,
    n_results: int = 5,
    category: str = None,
    city: str = None,
    request: Request = None,
    search_mode: str = "combined",
    user_lat: float = None,
    user_lng: float = None,
    pre_parsed: dict | ParsedQuery | None = None,
) -> list[dict]:
    """Run the hybrid place-search pipeline.

    search_mode:
        "combined" — RDB 필터 → ChromaDB 유사도 → 결합 스코어 (기본, 실서비스)
        "rdb_only" — RDB 필터링 + rule score만 사용 (평가용)
        "rag_only" — ChromaDB 의미 검색만 사용, RDB 사전 필터 없음 (평가용)

    user_lat / user_lng: 사용자 GPS 좌표. landmark가 없고 GPS가 제공되면
        현재 위치를 landmark_coords로 사용해 반경 검색을 수행.

    pre_parsed: 사전에 파싱된 쿼리 결과. 제공 시 LLM 파싱 호출을 건너뜀.
        dict는 평가용 입력, ParsedQuery는 채팅 핸들러에서 중복 파싱 방지용으로 사용.
    """
    try:
        if isinstance(pre_parsed, ParsedQuery):
            parsed = _clone_parsed(pre_parsed)
        elif pre_parsed:
            parsed = ParsedQuery(query)
            parsed.objective = deepcopy(pre_parsed["objective"])
            parsed.subjective = pre_parsed.get("subjective", query)
            parsed.time_condition = pre_parsed.get("time_condition")
            parsed.use_current_location = pre_parsed.get("use_current_location", False)
            parsed.landmark = pre_parsed.get("landmark")
            parsed.landmark_coords = pre_parsed.get("landmark_coords")
        else:
            parsed = await _parse_query_with_llm(query, request)

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

        if not requested_city or requested_city == SEOUL:
            if any(kw in query for kw in OUT_OF_SERVICE_KEYWORDS):
                logger.info(
                    f"[PlaceService] keyword-based out-of-service detected: {query} -> return empty result"
                )
                return []

        if await _is_unsupported_requested_place_type(query, parsed, db):
            logger.info(
                "[PlaceService] unsupported place type requested: %s -> return empty result",
                query,
            )
            return []

        if parsed.use_current_location:
            # LLM이 현재 위치 기반 검색으로 판단 → GPS 우선 사용
            parsed.landmark = None
            if user_lat and user_lng:
                parsed.landmark_coords = (user_lat, user_lng)
                logger.info(f"[PlaceService] use_current_location=True, GPS: ({user_lat}, {user_lng})")
        elif parsed.landmark:
            parsed.landmark_coords = await _get_landmark_coords(parsed.landmark)

        if not parsed.landmark_coords and user_lat and user_lng:
            parsed.landmark_coords = (user_lat, user_lng)
            logger.info(f"[PlaceService] fallback GPS coords: ({user_lat}, {user_lng})")

        if search_mode == "rdb_only":
            candidate_ids, parsed = await _filter_with_relaxation(
                parsed,
                db,
                max_candidates=RDB_FILTER_MAX_CANDIDATES,
            )
            candidate_ids = await _filter_candidate_ids_by_requested_place_type(
                candidate_ids, query, parsed, db
            )
            if _requires_requested_place_type_filter(query, parsed) and not candidate_ids:
                return []
            if parsed.time_condition:
                candidate_ids = await _filter_by_time(candidate_ids, parsed.time_condition, db)
            return await _fallback_rdb_only(parsed, candidate_ids, db, n_results)

        if search_mode == "rag_only":
            vector_results = await _search_by_chromadb(parsed, [], n_results, request)
            if vector_results:
                return await _fetch_and_score(vector_results, parsed, db, n_results)
            return []

        # combined (기존 로직)
        if _should_prioritize_outing(parsed):
            logger.info("[PlaceService] broad outing query detected, apply outing-first ranking")

        candidate_ids, parsed = await _filter_with_relaxation(
            parsed,
            db,
            max_candidates=RDB_FILTER_MAX_CANDIDATES,
        )
        candidate_ids = await _filter_candidate_ids_by_requested_place_type(
            candidate_ids, query, parsed, db
        )
        if _requires_requested_place_type_filter(query, parsed) and not candidate_ids:
            return []

        if parsed.time_condition:
            candidate_ids = await _filter_by_time(candidate_ids, parsed.time_condition, db)

        # Ablation A3: subjective가 비어 있어도 Chroma 재순위를 수행한다.
        # 기존에는 이 지점에서 RDB fallback으로 조기 반환했다.

        if (
            parsed.objective.get("is_indoor") is not None
            or parsed.objective.get("is_outdoor") is not None
        ):
            logger.info("[PlaceService] indoor/outdoor condition detected, skip ChromaDB re-ranking")
            return await _fallback_rdb_only(parsed, candidate_ids, db, n_results)

        # Ablation A2-1: Combined에서도 Chroma 후보를 RDB 후보 안으로 제한하지 않는다.
        # RAG 후보가 실제로 Combined 성능에 기여할 수 있는지 확인하기 위한 실험이다.
        vector_results = await _search_by_chromadb(
            parsed, [], n_results, request
        )

        if vector_results:
            places = await _fetch_and_score(vector_results, parsed, db, n_results)
            if places:
                if parsed.time_condition:
                    places = _sort_by_time_certainty(places, parsed.time_condition)
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
