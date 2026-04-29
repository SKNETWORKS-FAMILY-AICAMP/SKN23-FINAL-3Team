OWNER_TYPES = {
    "nature_lover": "🌿 자연 애호가",
    "city_explorer": "✨ 도시 감성러",
    "active_lifestyle": "🏃 활발한 활동가",
    "relaxed_healer": "🛋️ 느긋한 휴식러",
    "foodie_explorer": "🍴 맛집 탐방러",
}


class UserType:
    def __init__(self):
        self.types = OWNER_TYPES

    def get_type(self, type_id: str) -> str:
        return self.types.get(type_id, "")
