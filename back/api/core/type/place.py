import enum

PLACE_TYPE_MAP = {
    "12": "관광지",
    "14": "문화시설",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
    "39": "음식점",
}


# ── 지역명 키워드 매핑 ─────────────────────────────────────
DISTRICT_KEYWORDS_MAP = {
    "강남": "강남구", "강북": "강북구", "강서": "강서구", "강동": "강동구",
    "마포": "마포구", "홍대": "마포구", "서초": "서초구", "송파": "송파구",
    "용산": "용산구", "종로": "종로구", "중구": "중구", "성동": "성동구",
    "광진": "광진구", "동대문": "동대문구", "중랑": "중랑구", "성북": "성북구",
    "도봉": "도봉구", "노원": "노원구", "은평": "은평구", "서대문": "서대문구",
    "양천": "양천구", "구로": "구로구", "금천": "금천구", "영등포": "영등포구",
    "여의도": "영등포구",
    "동작": "동작구", "관악": "관악구", "강남구": "강남구",
}

CITY_KEYWORDS_MAP = {
    "서울": "서울특별시", "부산": "부산광역시", "대구": "대구광역시",
    "인천": "인천광역시", "광주": "광주광역시", "대전": "대전광역시",
    "울산": "울산광역시", "경기": "경기도", "강원": "강원도",
    "충북": "충청북도", "충남": "충청남도", "전북": "전라북도",
    "전남": "전라남도", "경북": "경상북도", "경남": "경상남도",
    "제주": "제주특별자치도",
}


class YNEnum(str, enum.Enum):
    """Y/N 여부 Enum."""
    Y = "Y"
    N = "N"


class FeeType(str, enum.Enum):
    """입장료/추가요금 정규화 타입.

    free        : 0원 또는 무료
    fixed       : 정수 금액 확정 (amount 컬럼에 원 단위)
    variable    : 변동/시기별/계절별/문의 (amount NULL)
    conditional : 성인/어린이 등 조건부 차등 (amount NULL)
    unknown     : 정규식·LLM 양쪽 모두 매칭 실패 (default)
    """
    free        = "free"
    fixed       = "fixed"
    variable    = "variable"
    conditional = "conditional"
    unknown     = "unknown"


class PlaceType:
    def __init__(self):
        self.types = PLACE_TYPE_MAP
        self.district_keywords = DISTRICT_KEYWORDS_MAP
        self.city_keywords = CITY_KEYWORDS_MAP

    def get_type(self, type_id: str) -> str:
        return self.types.get(type_id, "")

    def extract_location(self, query: str) -> dict:
        """쿼리에서 지역명 추출 → city + district 동시 반환 가능"""
        result = {}
        
        # city 먼저 추출
        for keyword, city in self.city_keywords.items():
            if keyword in query:
                result["city"] = city
                break
        
        # district 추출 (city와 독립적으로)
        for keyword, district in self.district_keywords.items():
            if keyword in query:
                result["district"] = district
                break
        
        return result
