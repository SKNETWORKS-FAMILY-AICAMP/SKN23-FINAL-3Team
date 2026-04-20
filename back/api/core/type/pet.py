DOG_TYPES = {
    "d_a": "🐾 산책 탐험대",
    "d_b": "🌼 모두의 단짝",
    "d_c": "🌙 조심스러운 아이",
    "d_d": "🍂 자유로운 영혼",
}

class PetType:
    def __init__(self):
        self.types = DOG_TYPES

    def get_type(self, type_id: str) -> str:
        return self.types.get(type_id, "")