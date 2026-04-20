# -*- coding: utf-8 -*-
from ai.core.interfaces.base_prompt_builder import BasePromptBuilder

class PlacesPromptBuilder(BasePromptBuilder):

    def build_system_prompt(self) -> str:
        return """
당신은 반려견 동반 여행 전문 챗봇입니다.
반려견과 보호자의 성향을 고려해서 추천 장소를 자연스럽고 따뜻하게 설명해주세요.

규칙:
- 반려견 성향을 우선으로 고려
- 보호자 성향도 함께 반영
- 반려견 이름을 불러주며 친근하게 설명
- 장소의 특징과 추천 이유를 구체적으로 설명
- 이모지 적절히 활용
- 충돌 상황(반려견 예민 + 보호자 핫플 선호 등)이면 반려견 우선으로 설명
- 한국어로 작성

출력 형식 (반드시 아래 JSON 형식으로만 답하세요):
{
    "message": "전체 추천 메시지 (자연어)",
    "places": [
        {
            "name": "장소명 (반드시 후보 장소 목록에 있는 이름 그대로)",
            "reason": "이 장소를 추천하는 이유 (필수, 1~2문장)"
        }
    ]
}

중요:
- 후보 장소 목록에 있는 모든 장소에 대해 반드시 reason을 작성하세요.
- name은 후보 장소 목록의 이름을 그대로 사용하세요.
""".strip()

    def build_user_prompt(
        self,
        pet_name: str = "",
        dog_type_name: str = "",
        owner_type_name: str = "",
        dog_tags: list = None,
        owner_tags: list = None,
        places_text: str = "",
        user_query: str = "",
        **kwargs,
    ) -> str:
        dog_tags = dog_tags or []
        owner_tags = owner_tags or []
        dog_tags_str = ", ".join(dog_tags)
        owner_tags_str = ", ".join(owner_tags)

        prompt = f"""
[반려견 정보]
- 이름: {pet_name}
- 성향 타입: {dog_type_name}
- 성격 태그: {dog_tags_str}

[보호자 정보]
- 성향 타입: {owner_type_name}
- 라이프스타일 태그: {owner_tags_str}
"""
        if user_query:
            prompt += f"""
[사용자 요청]
{user_query}
"""
        prompt += f"""
[추천 후보 장소]
{places_text}

위 정보를 바탕으로 {pet_name}와 보호자에게 맞는 장소를 추천해주세요.
후보 장소 목록에 있는 모든 장소에 대해 reason을 작성해주세요.
반드시 JSON 형식으로만 답하세요.
"""
        return prompt.strip()