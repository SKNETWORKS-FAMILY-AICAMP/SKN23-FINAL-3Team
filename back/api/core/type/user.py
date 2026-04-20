OWNER_TYPES = {
    "o_a": "🌿 자연 애호가",
    "o_b": "✨ 도시 감성러",
    "o_c": "🏃 활발한 활동가",
    "o_d": "🛋️ 느긋한 휴식러",
}

class UserType:
    def __init__(self):
        self.types = OWNER_TYPES

    def get_type(self, type_id: str) -> str:
        return self.types.get(type_id, "")