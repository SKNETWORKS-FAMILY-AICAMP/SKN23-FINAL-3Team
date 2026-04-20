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
