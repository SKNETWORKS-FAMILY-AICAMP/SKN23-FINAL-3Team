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
