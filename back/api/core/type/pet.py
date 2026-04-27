DOG_TYPES = {
    "outdoor_active": "🐾 산책 탐험대",
    "social_friendly": "🌼 모두의 단짝",
    "careful_pup": "🌙 조심스러운 아이",
    "free_spirited": "🍂 자유로운 영혼",
    "highly_sensitive": "🌺 예민한 감수성",
}


class PetType:
    def __init__(self):
        self.types = DOG_TYPES

    def get_type(self, type_id: str) -> str:
        return self.types.get(type_id, "")
