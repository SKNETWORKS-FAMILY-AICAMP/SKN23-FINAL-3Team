# -*- coding: utf-8 -*-
from datetime import date, datetime
from ai.core.interfaces.base_prompt_builder import BasePromptBuilder

class DiaryPromptBuilder(BasePromptBuilder):

    # 감정 이모지 → 문체 톤
    EMOTION_TONE: dict[str, str] = {
        "😊": "밝고 신나고 경쾌한 톤. 짧고 통통 튀는 문장. 기쁨이 넘침.",
        "😌": "잔잔하고 평온한 톤. 느긋하고 부드럽게 흘러가는 문장.",
        "🥹": "감성적이고 뭉클한 톤. 여운이 남는 문장. 살짝 감동적.",
        "😴": "나른하고 졸린 톤. 담백하고 느릿한 문장. 하루 마무리 느낌.",
        "😟": "살짝 걱정되고 세심한 톤. 조심스럽지만 부드럽게 마무리.",
        "🤍": "다정하고 애틋한 톤. 보호자에 대한 사랑이 자연스럽게 묻어남.",
    }

    # 일기 유형 → 강조 포인트
    DIARY_TYPE_FOCUS: dict[str, str] = {
        "dog":    "반려견의 행동, 컨디션, 먹은 것, 뛰어논 것 등 아이의 하루 자체에 집중",
        "owner":  "보호자와의 교감, 보호자가 느낀 감정, 함께한 순간의 따뜻함보다 편안한 유대감에 집중",
        "memory": "특별한 장면, 처음 경험, 여행 등 오래 기억될 순간에 집중",
        "daily":  "평범하지만 소중한 일상, 루틴한 하루의 작은 안정감과 행복에 집중",
    }

    # 감정 이모지 → 이미지 표정/장면 무드
    IMAGE_EMOTION_RULES: dict[str, str] = {
        "😊": (
            "gentle happy expression, "
            "curious and delighted mood, "
            "bright readable emotion, "
            "subtle smile, "
            "sparkling lively eyes, "
            "light playful energy"
        ),
        "😌": (
            "peaceful and calm expression, "
            "soft relaxed eyes, "
            "gentle small smile, "
            "quiet comfortable mood, "
            "restful peaceful energy"
        ),
        "🥹": (
            "tender emotional expression, "
            "gentle sparkling eyes, "
            "soft heartfelt mood, "
            "slightly dreamy but calm atmosphere"
        ),
        "😴": (
            "sleepy relaxed expression, "
            "soft droopy eyes, "
            "quiet slow mood, "
            "restful cozy energy"
        ),
        "😟": (
            "slightly cautious but gentle expression, "
            "soft concerned mood, "
            "subtle emotional tension, "
            "still calm and tender atmosphere"
        ),
        "🤍": (
            "affectionate and loving expression, "
            "gentle warm eyes, "
            "soft smile, "
            "deeply tender and peaceful mood"
        ),
    }

    # 해외 키워드
    OVERSEAS_KEYWORDS = [
        "해외여행", "해외", "외국", "일본", "도쿄", "오사카", "미국", "뉴욕",
        "파리", "프랑스", "유럽", "태국", "방콕", "베트남", "하노이", "호치민",
        "스페인", "이탈리아", "영국", "런던", "중국", "홍콩", "대만", "타이페이",
    ]

    # ── BasePromptBuilder 필수 구현 ──────────────────────

    def build_system_prompt(self) -> str:
        """일기 생성용 시스템 프롬프트 (현재 미사용, 인터페이스 규칙 충족용)"""
        return "너는 강아지의 하루를 대신 써주는 그림일기 작가다."

    def build_user_prompt(self, **kwargs) -> str:
        """일기 생성용 유저 프롬프트 — build_diary_prompt() 호출"""
        return self.build_diary_prompt(**kwargs)

    # ── 공개 메서드 ──────────────────────────────────────

    def build_diary_prompt(
        self,
        pet_name: str,
        breed: str,
        birth_date: str | None,
        personalities: list[str],
        diary_type: str,
        emotion: str,
        conversation_summary: str,
        owner_name: str = "",
        **kwargs,
    ) -> str:
        age_years = self._get_pet_age_years(birth_date)
        age_text = f"{age_years}살" if age_years is not None else "나이 정보 없음"
        personality_text = ", ".join(personalities) if personalities else "귀엽고 사랑스러움"
        tone = self.EMOTION_TONE.get(emotion, self.EMOTION_TONE["😊"])
        focus = self.DIARY_TYPE_FOCUS.get(diary_type, self.DIARY_TYPE_FOCUS["dog"])
        scene_hint = self._infer_scene_hint(conversation_summary)
        image_emotion_rule = self.IMAGE_EMOTION_RULES.get(emotion, self.IMAGE_EMOTION_RULES["😊"])
        owner_label = owner_name.strip() if owner_name and owner_name.strip() else "보호자"

        return f"""
너는 강아지의 하루를 대신 써주는 그림일기 작가다.

[핵심 역할]
보호자와 나눈 대화를 바탕으로,
강아지 {pet_name}가 직접 일기장에 쓴 것처럼
순수하고 사랑스럽고 귀여운 일기를 작성한다.

[절대 규칙]
- 반드시 1인칭 강아지 시점 ("나는", "내가", "오늘 나는")
- 화자는 {pet_name}이며, 강아지다
- 사람은 절대 강아지처럼 표현하지 않는다
- 등장하는 강아지는 {pet_name} 한 마리뿐
- 보호자 호칭은 "{owner_label}"로 통일 (예: "{owner_label}이", "{owner_label}가", "{owner_label}랑")
- "멍!"은 정확히 한 번만 사용
- 사실에 없는 내용은 지어내지 않는다

[말투 규칙 - 가장 중요]
- 어린아이가 쓴 일기장처럼 맑고 귀엽고 솔직하게
- 강아지 특유의 엉뚱한 시선과 순수한 감정 포함
- 짧고 리듬감 있는 문장
- 억지 감동 금지, 자연스럽고 사랑스럽게

[감정 톤 - 선택된 이모지: {emotion}]
{tone}

[일기 유형: {diary_type}]
이 유형의 강조 포인트: {focus}

[내용 구성]
- 본문 최소 300자, 5~7문장
- 기승전결 흐름 (시작 → 상황 → 행동/감정 → 마무리)
- 감각 묘사 2개 이상 필수 (냄새 / 촉감 / 소리 / 움직임 중)
- 마지막 문장은 포근하고 사랑스럽게

[강아지 정보]
이름: {pet_name}
나이: {age_text}
견종: {breed or "강아지"}
성격: {personality_text}

[오늘의 대화 내용]
{conversation_summary}

[이미지 장면 힌트]
{scene_hint}

[이미지 감정/표정 힌트]
{image_emotion_rule}

[이미지 프롬프트 생성 규칙]
- image_prompt_base는 오늘의 핵심 장면을 영어로 설명하되, 반드시 "일기 내용과 맞는 장면"이 되도록 쓴다
- 정적인 증명사진 같은 정면샷보다, 행동과 상황이 보이는 서사적인 장면을 우선한다
- 장면 설명에는 위치, 행동, 감정, 분위기, 감각 단서가 포함되어야 한다
- 아래 요소를 자연스럽게 포함한다:
  one cute storybook dog as the main character,
  simple rounded face,
  small evenly spaced eyes,
  one small clear nose,
  tiny readable mouth,
  symmetrical facial features,
  clean silhouette,
  face fully rendered,
  lively readable expression,
  polished premium children's book illustration quality,
  soft storybook illustration,
  gouache and colored pencil texture,
  calm pastel palette with soft greens and blues,
  natural soft daylight,
  peaceful and comfortable atmosphere,
  clean white fur if the dog is white,
  avoid yellow cast,
  avoid sepia tone,
  no blurry face,
  no distorted facial features,
  no extra animals
- 배경보다 캐릭터 가독성이 우선이지만, 배경도 일기 장면과 어울리게 서사를 전달해야 한다
- 실사풍이 아니라 그림책 캐릭터 일러스트 느낌으로 쓴다
- 전체 색감은 노랗거나 세피아처럼 치우치지 않게 한다

[출력 형식 - 반드시 JSON으로만, 다른 말 금지]
{{
  "title": "귀엽고 짧은 제목 (15자 이내, 강아지 말투)",
  "content": "일기 본문 (300자 이상, 강아지 1인칭, 귀엽고 감각적으로)",
  "summary": "한줄요약 (30자 이내, 귀엽게)",
  "image_prompt_base": "Describe the most vivid storybook scene from today's diary in English within 90 words. The image must be a single scene, single panel illustration — never a comic strip, never multi-panel, never split into 2 or 4 frames. Show one cute storybook dog as the main character with a simple rounded face, small clear eyes, one small nose, tiny readable mouth, and a lively expressive face. Prefer a narrative scene over a static portrait. Include environmental storytelling, polished premium children's book illustration quality, gouache and colored pencil texture, calm pastel palette with soft greens and blues, natural soft daylight, peaceful and comfortable atmosphere, clean white fur if the dog is white, avoid yellow cast, and no blurry or distorted face."
}}
"""

    def build_final_image_prompt(
        self,
        image_prompt_base: str,
        breed: str,
        breed_en: str | None,
        birth_date: str | None,
        personalities: list[str],
        all_answers: list[str],
        emotion: str = "😊",
    ) -> str:
        breed_name = breed_en or breed or "small dog"
        personality = ", ".join(personalities) if personalities else "cute and lovely"
        age_style = self._get_age_based_art_style(birth_date)
        age_appearance = self._get_age_appearance_hint(birth_date)
        overseas_location = self._detect_overseas(all_answers)
        image_emotion_rule = self.IMAGE_EMOTION_RULES.get(emotion, self.IMAGE_EMOTION_RULES["😊"])
        fur_color_rule = self._get_fur_color_rule(breed, image_prompt_base, all_answers)

        face_rules = (
            "storybook character design, "
            "simple rounded face, "
            "small evenly spaced eyes, "
            "one small clear nose, "
            "tiny readable mouth, "
            "symmetrical facial features, "
            "clean face shape, "
            "clear lively expression, "
            "face fully rendered, "
            "not blurry, "
            "not smudged, "
            "no distorted face, "
            "no duplicated eyes, "
            "no extra ears, "
            "no extra limbs"
        )

        all_characters_face_rules = (
            "every character in the scene must have a clearly drawn face, "
            "all dogs including background dogs must have simple clean readable faces, "
            "no blurry dog faces anywhere in the image, "
            "no smudged or undefined dog faces, "
            "background dogs should be smaller and simplified but still clearly drawn, "
            "IMPORTANT — human faces: draw all humans in a very simple flat storybook style, "
            "human faces must use minimal features — simple oval face, dot eyes, small curved mouth, "
            "no detailed realistic human faces, "
            "keep human faces extremely simplified like a children's picture book, "
            "if a human face cannot be drawn clearly, show the human from the side or back, "
            "no blurry human faces, "
            "no creepy uncanny human faces, "
            "no faceless humans"
        )

        expression_rules = (
            f"{image_emotion_rule}, "
            "bright readable emotion, "
            "subtle expressive face, "
            "emotion should match the diary mood"
        )

        composition_rules = (
            "single scene illustration, "
            "single panel only, "
            "one cohesive scene, "
            "narrative storybook scene, "
            "character readability first, "
            "large clear main subject, "
            "full body of the main dog must be fully visible within the frame, "
            "entire dog including tail must be inside the image, "
            "leave enough margin around the dog so no body part is cropped, "
            "the action and environment must match the diary content, "
            "avoid static passport-like front pose, "
            "environmental storytelling, "
            "picture-book layout, "
            "balanced composition, "
            "background supports the story, "
            "main character remains the clearest element, "
            "no comic strips, "
            "no manga panels, "
            "no multi-panel layout, "
            "no split panels, "
            "no panel borders, "
            "no 2-panel, "
            "no 4-panel, "
            "no sequential frames, "
            "no grid layout"
        )

        quality_rules = (
            "polished high-quality children's book illustration, "
            "premium illustration quality, "
            "refined character rendering, "
            "clean facial drawing, "
            "all props and objects clearly rendered with clean defined shapes, "
            "toys and items must have readable clean outlines, "
            "no blurry or undefined objects, "
            "finished composition, "
            "soft but well-designed background, "
            "detailed yet gentle environment, "
            "professional picture-book artwork, "
            "visually cohesive and aesthetically refined"
        )

        texture_rules = (
            "STYLE: Korean-Japanese soft storybook illustration, "
            "soft gouache and colored pencil texture, "
            "matte hand-painted storybook finish, "
            "clean soft shading, "
            "delicate grain texture, "
            "calm muted pastel palette — sage green, misty green, powder blue, airy sky blue, ivory white, soft neutral beige, "
            "soft natural daylight, "
            "gentle warm-neutral tone, "
            "avoid vivid saturated colors, "
            "avoid strong yellow cast, "
            "avoid sepia tone, "
            "avoid orange lighting, "
            "avoid overly warm color grading, "
            "avoid Western cartoon style, "
            "avoid bright primary colors, "
            "preserve soft muted pastels and clean whites"
        )

        mood_rules = (
            "wholesome storybook animal character, "
            "wholesome diary illustration, "
            "peaceful and comfortable atmosphere, "
            "fresh and airy color mood, "
            "soft emotionally calm feeling, "
            "clean and balanced scene, "
            "not realistic fur detail, "
            "not photorealistic, "
            "not overly detailed realism"
        )

        if overseas_location:
            location_suffix = (
                f"setting inspired by {overseas_location}, "
                f"authentic local scenery, "
                f"travel diary feeling, "
                f"balanced calm pastel colors"
            )
        else:
            location_suffix = (
                "Korean everyday setting if applicable, "
                "soft natural daylight, "
                "fresh airy atmosphere, "
                "balanced calm pastel colors, "
                "sage green and powder blue background accents, "
                "no Middle Eastern architecture, "
                "no mosque, "
                "no Arabic text"
            )

        return (
            f"{image_prompt_base.strip().rstrip('.')}, "
            f"main character: one adorable {breed_name}, "
            f"personality in expression: {personality}, "
            f"{age_style}, "
            f"{(age_appearance + ', ') if age_appearance else ''}"
            f"{fur_color_rule}, "
            f"{face_rules}, "
            f"{all_characters_face_rules}, "
            f"{expression_rules}, "
            f"{composition_rules}, "
            f"{quality_rules}, "
            f"{texture_rules}, "
            f"{mood_rules}, "
            f"{location_suffix}, "
            f"all humans are East Asian in appearance if humans appear"
        )

    # ── private 메서드 ────────────────────────────────────

    def _get_pet_age_months(self, birth_date_str: str | None) -> int | None:
        if not birth_date_str:
            return None
        try:
            birth = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
        except ValueError:
            return None
        today = date.today()
        months = (today.year - birth.year) * 12 + (today.month - birth.month)
        if today.day < birth.day:
            months -= 1
        return max(months, 0)

    def _get_pet_age_years(self, birth_date_str: str | None) -> int | None:
        months = self._get_pet_age_months(birth_date_str)
        return months // 12 if months is not None else None

    def _get_age_based_art_style(self, birth_date_str: str | None) -> str:
        age_months = self._get_pet_age_months(birth_date_str)

        base = (
            "high-quality storybook illustration, "
            "premium children's book art, "
            "cute character design with refined rendering, "
            "simple rounded face, "
            "clean silhouette, "
            "readable facial features, "
            "small clear eyes, "
            "one small clear nose, "
            "tiny readable mouth, "
            "symmetrical facial features, "
            "soft gouache and colored pencil texture, "
            "matte hand-painted feeling, "
            "delicate grain texture, "
            "clean layered color blocking, "
            "calm pastel palette, "
            "soft sage green, misty green, powder blue, airy sky blue, ivory white, soft neutral beige, "
            "natural soft daylight, "
            "peaceful and comfortable atmosphere, "
            "airy and fresh mood, "
            "emotionally gentle, "
            "polished illustration finish, "
            "not realistic, "
            "not photorealistic, "
            "avoid strong yellow cast, "
            "avoid sepia tone, "
            "avoid orange lighting, "
            "avoid overly warm color grading, "
            "prefer neutral and clean whites"
        )

        if age_months is None:
            return base
        if age_months <= 5:
            return base + ", baby-like proportions, round head, short muzzle, very soft fluffy feeling, innocent and playful"
        if age_months <= 11:
            return base + ", young puppy energy, bright but calm, slightly puffy proportions"
        if age_months <= 35:
            return base + ", balanced youthful proportions, storybook polish, gentle simplified details"
        return base + ", slightly calmer and more refined, emotionally gentle, soft mature storybook quality"

    def _get_age_appearance_hint(self, birth_date_str: str | None) -> str:
        age_months = self._get_pet_age_months(birth_date_str)
        if age_months is None:
            return ""
        if age_months <= 11:
            return "playful bouncy pose, curious and excited energy, innocent baby-like expression"
        if age_months <= 35:
            return "lively energetic posture, youthful active movement, bright curious expression"
        if age_months <= 71:
            return "calm composed posture, relaxed confident stance, gentle mature expression"
        return "slow calm relaxed posture, peaceful serene expression, gentle dignified and wise mood"

    def _detect_overseas(self, answers: list[str]) -> str | None:
        full_text = " ".join(answers)
        for kw in self.OVERSEAS_KEYWORDS:
            if kw in full_text:
                return kw
        return None

    def _infer_scene_hint(self, conversation_summary: str) -> str:
        text = conversation_summary or ""
        if any(kw in text for kw in ["바다", "해변", "파도", "모래", "부산"]):
            return "The main scene should show the dog experiencing the seaside, with shallow waves, beach, sea breeze, and a curious or delighted reaction."
        if any(kw in text for kw in ["공원", "잔디", "풀", "산책", "벚꽃"]):
            return "The main scene should show the dog outdoors in a park or on a walk, with grass, breeze, and visible movement or interest in the surroundings."
        if any(kw in text for kw in ["소파", "집", "거실", "기대", "옆에", "안겨", "무릎"]):
            return "The main scene should show a cozy indoor moment with the dog near the guardian, with closeness, comfort, and emotional bonding."
        if any(kw in text for kw in ["카페", "여행", "기차", "전철", "버스", "외출"]):
            return "The main scene should show a special outing or travel moment, with environmental storytelling and a memorable but calm atmosphere."
        return "The main scene should clearly match the most vivid emotional moment from the diary, showing the dog's action, mood, and surroundings in a narrative way."

    def _get_fur_color_rule(self, breed: str, image_prompt_base: str, all_answers: list[str]) -> str:
        text = " ".join([breed or "", image_prompt_base or "", *all_answers]).lower()
        white_keywords = [
            "white", "ivory", "cream", "white dog", "bichon", "maltese", "spitz", "samoyed",
            "비숑", "말티즈", "스피츠", "사모예드", "흰", "하얀", "백색"
        ]
        if any(kw in text for kw in white_keywords):
            return (
                "fur color must remain clearly white, "
                "clean neutral white fur, "
                "soft ivory white highlights only, "
                "no yellow fur tint, "
                "no beige fur cast, "
                "no cream-colored body unless explicitly described, "
                "preserve bright white character readability"
            )
        return "natural fur color, clean readable coat color, avoid muddy color cast"