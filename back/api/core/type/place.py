import enum

PLACE_TYPE_MAP = {
    "12": "관광지",
    "14": "문화시설",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
    "39": "음식점",
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
    FREE = "free"
    FIXED = "fixed"
    VARIABLE = "variable"
    CONDITIONAL = "conditional"
    UNKNOWN = "unknown"


class PlaceType:
    def __init__(self):
        self.types = PLACE_TYPE_MAP

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
