# -*- coding: utf-8 -*-
from datetime import date, datetime
from ai.core.interfaces.base_prompt_builder import BasePromptBuilder

class DiaryPromptBuilder(BasePromptBuilder):

    # ── 감정 이모지 → 문체 톤 ──────────────────────────
    EMOTION_TONE: dict[str, str] = {
        "😊": "밝고 신나고 경쾌한 톤. 짧고 통통 튀는 문장. 기쁨이 넘침.",
        "😌": "잔잔하고 평온한 톤. 느긋하고 부드럽게 흘러가는 문장.",
        "🥹": "감성적이고 뭉클한 톤. 여운이 남는 문장. 살짝 감동적.",
        "😴": "나른하고 졸린 톤. 담백하고 느릿한 문장. 하루 마무리 느낌.",
        "😟": "살짝 걱정되고 세심한 톤. 조심스럽지만 부드럽게 마무리.",
        "🤍": "다정하고 애틋한 톤. 보호자에 대한 사랑이 자연스럽게 묻어남.",
    }

    # ── 일기 유형 → 강조 포인트 ────────────────────────
    DIARY_TYPE_FOCUS: dict[str, str] = {
        "dog":    "반려견의 행동, 컨디션, 먹은 것, 뛰어논 것 등 아이의 하루 자체에 집중",
        "owner":  "보호자와의 교감, 함께한 순간의 편안한 유대감에 집중",
        "memory": "특별한 장면, 처음 경험, 여행 등 오래 기억될 순간에 집중",
        "daily":  "평범하지만 소중한 일상, 루틴한 하루의 작은 안정감과 행복에 집중",
    }

    # ── 견종 영문명 자동 매핑 ─────────────────────────
    BREED_EN_MAP: dict[str, str] = {
        "골든 리트리버": "Golden Retriever", "말티즈": "Maltese", "포메라니안": "Pomeranian",
        "비숑 프리제": "Bichon Frise", "시바이누": "Shiba Inu", "진도견": "Jindo",
        "닥스훈트": "Dachshund", "웰시코기": "Welsh Corgi Pembroke", "시츄": "Shih Tzu",
        "보더콜리": "Border Collie", "사모예드": "Samoyed", "허스키": "Siberian Husky",
        "라브라도 리트리버": "Labrador Retriever", "치와와": "Chihuahua", "아키타견": "Akita",
        "비글": "Beagle", "페키니즈": "Pekingese", "재패니즈 스피츠": "Japanese Spitz",
        "그레이하운드": "Greyhound", "푸들": "Poodle", "스피츠": "Japanese Spitz",
        "불독": "English Bulldog", "프렌치 불독": "French Bulldog", "요크셔 테리어": "Yorkshire Terrier",
        "슈나우저": "Miniature Schnauzer", "달마시안": "Dalmatian", "도베르만": "Doberman",
        "셰퍼드": "German Shepherd", "삽살개": "Sapsali", "풍산개": "Pungsan",
    }

    # ── 견종별 시각적 특징 힌트 ────────────────────────
    BREED_VISUAL_HINTS: dict[str, str] = {
        "Poodle": "with clearly curly fluffy coat — NOT straight fur, elegant posture",
        "Akita": "with large powerful muscular body, thick double coat, broad dignified face, erect triangular ears",
        "Greyhound": "with slim elegant long body, narrow long snout, long slender legs, expressive gentle eyes",
        "Shih Tzu": "with very flat face, long flowing silky coat, and large round dark eyes",
        "Dachshund": "with distinctively very long body, very short legs, and long floppy ears",
        "Pekingese": "with flat wrinkled face, thick lion-like mane coat, small compact body",
        "Samoyed": "with thick fluffy white double coat, black eyes and nose, gentle smile — maintain realistic dog proportions, avoid overly chibi",
        "Siberian Husky": "with striking bi-color or blue eyes, thick coat, wolf-like facial markings",
        "Border Collie": "with black and white coat, alert intelligent expression, medium build",
        "Welsh Corgi Pembroke": "with short legs, long body, large upright ears, fluffy hindquarters",
        "Bichon Frise": "with round fluffy white coat, dark eyes and nose, small compact body",
        "Maltese": "with long silky white straight coat, tiny delicate build",
        "Jindo": "with medium build, wedge-shaped face, erect ears, curled tail, often white or tan coat",
        "Cocker Spaniel": "with long wavy silky ears, medium-length wavy coat, gentle round eyes, compact soft body",
        "German Shepherd": "with tan and black saddle coat, large upright pointed ears, confident athletic medium-large build, alert intelligent expression",
        "French Bulldog": "with very flat wrinkled face, large upright bat-like ears, compact muscular body, short smooth coat",
        "Yorkshire Terrier": "with fine silky steel-blue and tan coat, small delicate build, confident perky expression, small erect V-shaped ears",
        "Miniature Schnauzer": "with distinctive bushy eyebrows and beard, salt-and-pepper wiry coat, compact sturdy rectangular build",
        "Dalmatian": "with white short coat covered in clearly defined black spots, athletic medium-large build, alert lively expression",
        "Sapsali": "with very long thick shaggy coat covering face and body, medium-large sturdy build, gentle calm expression — long straight flowing fur",
    }

    # ── 야간 키워드 ──────────────────────────────────
    NIGHT_KEYWORDS = [
        "밤", "저녁", "야간", "잠들기 전", "자기 전", "잠자리", "취침",
        "불 끄고", "조명 켜고", "램프", "어두워", "어둑", "달빛",
        "night", "evening", "bedtime", "before sleep",
    ]

    # ── 해외 키워드 ───────────────────────────────────
    OVERSEAS_KEYWORDS = [
        "해외여행", "해외", "외국", "일본", "도쿄", "오사카", "미국", "뉴욕",
        "파리", "프랑스", "유럽", "태국", "방콕", "베트남", "하노이", "호치민",
        "스페인", "이탈리아", "영국", "런던", "중국", "홍콩", "대만", "타이페이",
    ]

    # ── 감정 이모지 → 이미지 표정 무드 ──────────────────
    IMAGE_EMOTION_RULES: dict[str, str] = {
        "😊": "gentle happy expression, sparkling lively eyes, light playful energy",
        "😌": "peaceful calm expression, soft relaxed eyes, quiet comfortable mood",
        "🥹": "tender emotional expression, gentle sparkling eyes, soft heartfelt mood",
        "😴": "sleepy relaxed expression, soft droopy eyes, restful cozy energy",
        "😟": "slightly cautious but gentle expression, soft concerned mood, calm tender atmosphere",
        "🤍": "affectionate loving expression, gentle warm eyes, deeply tender peaceful mood",
    }

    # ── BasePromptBuilder 필수 구현 ──────────────────────

    def build_system_prompt(self) -> str:
        return "너는 강아지의 하루를 대신 써주는 프리미엄 그림일기 작가다."

    def build_user_prompt(self, **kwargs) -> str:
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
        owner_gender: str = "",
        **kwargs,
    ) -> str:
        age_years = self._get_pet_age_years(birth_date)
        age_text = f"{age_years}살" if age_years is not None else "나이 정보 없음"
        personality_text = ", ".join(personalities) if personalities else "귀엽고 사랑스러움"
        tone = self.EMOTION_TONE.get(emotion, self.EMOTION_TONE["😊"])
        focus = self.DIARY_TYPE_FOCUS.get(diary_type, self.DIARY_TYPE_FOCUS["dog"])
        scene_hint = self._infer_scene_hint(conversation_summary)
        image_emotion_rule = self.IMAGE_EMOTION_RULES.get(emotion, self.IMAGE_EMOTION_RULES["😊"])
        time_of_day = self._detect_time_of_day([conversation_summary])
        time_hint = (
            "nighttime scene, soft indoor lamp light or moonlight, cozy dim atmosphere, "
            if time_of_day == "night"
            else "natural soft daylight, "
        )

        if owner_name and owner_name.strip():
            owner_label = owner_name.strip()
        elif owner_gender.upper() == "MALE":
            owner_label = "보호자 아빠"
        elif owner_gender.upper() == "FEMALE":
            owner_label = "보호자 엄마"
        else:
            owner_label = "보호자"

        return f"""
너는 강아지의 하루를 대신 써주는 프리미엄 그림일기 작가다.
보호자와 나눈 대화를 바탕으로, 강아지 {pet_name}가 직접 쓴 것처럼 순수하고 사랑스러운 일기를 작성한다.
출력은 반드시 JSON만 한다.

[절대 규칙]
- 반드시 1인칭 강아지 시점 ("나는", "내가", "오늘 나는")
- 화자는 {pet_name}(강아지)이며, 사람은 절대 강아지처럼 표현하지 않는다
- 등장하는 강아지는 {pet_name} 한 마리뿐이다
- 보호자 호칭은 "{owner_label}" 그대로 사용하고 이름 자체를 변형하지 않는다
  예) 이름이 "노랑"이면: 노랑은/노랑이/노랑을 (O), 노랑랑/노랑이랑 (X)
- "멍!"은 정확히 한 번만 사용한다
- 사실에 없는 사건, 장소, 음식, 행동, 감정은 지어내지 않는다
- 병, 상처, 위험, 공격성 같은 내용은 대화에 있을 때만 반영한다
- 견종, 나이, 성격 정보가 있으면 자연스럽게 반영하되 과장하지 않는다

[문체]
- 어린아이가 쓴 일기처럼 맑고 귀엽고 솔직한 말투
- 강아지 특유의 엉뚱한 시선과 순수한 감정
- 짧고 리듬감 있는 문장
- 과한 시적 표현, 사람스러운 철학적 문장, 번역체 금지

[감정 톤: {emotion}]
{tone}

[일기 유형: {diary_type}]
{focus}

[내용 구성]
- 본문 최소 300자
- 5~7문장
- 기승전결이 느껴지는 자연스러운 흐름
- 감각 묘사 2개 이상 포함 (냄새/촉감/소리/움직임 중)
- 마지막 문장은 포근하고 사랑스럽게 마무리
- 하루 전체를 나열하기보다 가장 기억에 남는 순간 중심으로 쓴다

[강아지 정보]
이름: {pet_name} | 나이: {age_text} | 견종: {breed or "강아지"} | 성격: {personality_text}

[오늘의 대화 내용]
{conversation_summary}

[이미지 힌트]
{scene_hint}
표정/감정: {image_emotion_rule}

[image_prompt_base 생성 규칙]
- 반드시 영어로 작성
- 90단어 이내
- 하루 전체 요약 금지
- 가장 선명한 하나의 순간만 묘사
- 정적 정면샷 금지
- 행동과 상황이 보이는 서사적 장면으로 작성
- 위치, 행동, 감정, 분위기를 포함
- {time_hint}full-page picture book illustration 느낌으로 작성
- one cute dog as the main character
- one continuous moment from one camera view
- one single full-bleed illustration
- CRITICAL: pick ONE single frozen moment — do NOT illustrate before/after or two separate locations
- CRITICAL: exactly one dog appears — do NOT show the same dog twice in different poses
- no multi-panel, no split screen, no comic strip, no manga layout
- no frames, no borders, no panel dividers, no grid layout
- do not divide the page into multiple scenes
- never depict mirror reflections or window reflections of the dog
- if a guardian appears, the guardian is secondary and should not dominate the scene

[출력 형식 - 반드시 JSON만]
{{
  "title": "귀엽고 짧은 제목 (15자 이내, 강아지 말투)",
  "content": "일기 본문 (300자 이상, 강아지 1인칭)",
  "summary": "한줄요약 (30자 이내, 귀엽게)",
  "image_prompt_base": "English only. One single storybook scene within 90 words. One cute dog as the main character. Narrative single moment, not a static portrait, not a collage, not multiple scenes."
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
        owner_gender: str = "",
        **kwargs,
    ) -> str:
        breed_name = self._get_breed_en(breed, breed_en)
        breed_hint = self._get_breed_visual_hint(breed_name)
        personality = ", ".join(personalities) if personalities else "cute and lovely"
        age_style = self._get_age_based_art_style(birth_date)
        age_appearance = self._get_age_appearance_hint(birth_date)
        overseas_location = self._detect_overseas(all_answers)
        image_emotion_rule = self.IMAGE_EMOTION_RULES.get(emotion, self.IMAGE_EMOTION_RULES["😊"])
        fur_color_rule = self._get_fur_color_rule(breed, image_prompt_base, all_answers)
        time_of_day = self._detect_time_of_day(all_answers + [image_prompt_base])

        if owner_gender.upper() == "MALE":
            guardian_gender_hint = "if a guardian appears, they appear as a man — male guardian"
        elif owner_gender.upper() == "FEMALE":
            guardian_gender_hint = "if a guardian appears, they appear as a woman — female guardian"
        else:
            guardian_gender_hint = ""

        subject_priority_rules = (
            "PRIORITY ORDER: first the main dog's face and body readability, "
            "second the dog's action and emotion, "
            "third the immediate environment, "
            "fourth any human or background details, "
            "the dog must remain the clear visual focal point of the entire image, "
            "if humans appear, they must stay secondary and visually simpler than the dog"
        )

        face_rules = (
            "PRIORITY: the dog's face must be the clearest and most carefully rendered element in the image, "
            "simple rounded storybook dog face with fully distinct readable features, "
            "two clear symmetrical eyes, one small clear nose, one tiny readable mouth, "
            "clean muzzle shape, clean ear shapes, clear facial silhouette, "
            "no blurry face, no smudged face, no melted face, no distorted or asymmetrical features, "
            "no duplicated eyes, no extra nose, no extra ears, no extra limbs, "
            "avoid extreme chibi or super-deformed proportions, keep believable dog proportions"
        )

        human_rules = (
            "all humans MUST use the same soft storybook illustration style as the dog, "
            "absolutely no photorealistic human faces, "
            "human faces should be simple rounded storybook faces — visible and readable but not realistic, "
            "small clear dot eyes, tiny curved smile, soft oval face shape, "
            "all humans are East Asian with black or dark brown eyes — no blue or green eyes, "
            "background humans may be slightly smaller but must still have a clear readable storybook face — NOT silhouette, NOT blurred, "
            "human faces must be clean and distinguishable even in the background, "
            "if a human is very far in the background show them from the side or back rather than blurring the face, "
            "human hands should be simplified, soft, partially hidden if needed, "
            "avoid detailed fingers, avoid complex hand poses, avoid hands close to the camera"
        )

        composition_rules = (
            "ABSOLUTE: one single frozen moment in time — never show two locations or two time periods in one image, "
            "ABSOLUTE: EXACTLY ONE dog in the entire image — do NOT show the same dog twice in different poses or moments, "
            "single scene only, single panel only, "
            "one continuous full-page illustration from a single camera view, "
            "no comic strip, no multi-panel, no split screen, no manga layout, "
            "no collage, no storyboard, no sequence of moments, "
            "no frames, no borders, no panel dividers, no boxed sections, no grid layout, "
            "do not divide the page into multiple scenes, "
            "background must belong to the same single moment, not separate mini-scenes, "
            "narrative single moment over static portrait, "
            "balanced picture-book composition, "
            "full body of the main dog preferably visible unless a closer crop is needed for face clarity, "
            "no body parts awkwardly cropped, "
            "no extra dogs or animals unless explicitly mentioned in the story, "
            "render any mirror as blank or facing away — never show the dog reflected in a mirror or window, "
            "no ghost images, no duplicated character, no reflection animal"
        )

        quality_rules = (
            "premium polished children's picture book illustration, "
            "clean readable outlines, readable props and objects, "
            "clear character silhouette, "
            "finished professional composition, "
            "soft hand-painted texture, "
            "not photorealistic, not 3D render, not plastic, not hyper-detailed realism"
        )

        if time_of_day == "night":
            texture_rules = (
                "STYLE: Korean-Japanese soft picture book illustration, "
                "soft gouache and colored pencil texture, matte hand-painted finish, "
                "nighttime palette — deep navy, dusty indigo, muted lavender, soft charcoal, warm ivory glow, "
                "gentle indoor lamp light or soft moonlight, cozy calm dim atmosphere, "
                "avoid bright daylight, avoid orange cast, avoid sepia tone, avoid harsh contrast, avoid Western cartoon style"
            )
        else:
            texture_rules = (
                "STYLE: Korean-Japanese soft picture book illustration, "
                "soft gouache and colored pencil texture, matte hand-painted finish, "
                "calm pastel palette — sage green, powder blue, ivory white, soft neutral beige, "
                "soft natural daylight, gentle warm-neutral tone, "
                "avoid vivid saturation, avoid yellow cast, avoid sepia tone, avoid harsh contrast, avoid Western cartoon style"
            )

        if overseas_location:
            location_suffix = (
                f"setting inspired by {overseas_location}, authentic local scenery, "
                "travel diary feeling, calm balanced colors"
            )
        else:
            location_suffix = (
                "Korean everyday setting if applicable, "
                "no Middle Eastern architecture, no mosque, no Arabic text"
            )

        return (
            f"{image_prompt_base.strip().rstrip('.')}, "
            f"main character: one adorable {breed_name}{(' ' + breed_hint) if breed_hint else ''}, "
            f"personality in expression: {personality}, "
            f"{age_style}, "
            f"{(age_appearance + ', ') if age_appearance else ''}"
            f"{fur_color_rule}, "
            f"{subject_priority_rules}, "
            f"{face_rules}, "
            f"{human_rules}, "
            f"{image_emotion_rule}, emotion matches diary mood exactly, "
            f"{composition_rules}, "
            f"{quality_rules}, "
            f"{texture_rules}, "
            f"{location_suffix}, "
            f"all humans are East Asian with black or dark brown eyes if humans appear, "
            f"{(guardian_gender_hint + ', ') if guardian_gender_hint else ''}"
            f"no visible text or letters anywhere in the image — no text on food, objects, props, or backgrounds"
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
            "premium children's picture book art, "
            "soft gouache and colored pencil texture, "
            "matte hand-painted feeling, "
            "delicate grain texture, "
            "calm pastel palette — soft sage green, powder blue, ivory white, soft neutral beige, "
            "emotionally gentle and warm, "
            "not realistic, not photorealistic, "
            "avoid strong yellow cast, avoid sepia tone, avoid orange lighting, avoid plastic 3D look"
        )
        if age_months is None:
            return base
        if age_months <= 5:
            return base + ", baby-like proportions, round head, short muzzle, very soft fluffy feeling, innocent and playful"
        if age_months <= 11:
            return base + ", young puppy energy, bright but calm, slightly puffy proportions"
        if age_months <= 35:
            return base + ", balanced youthful proportions, storybook polish, gentle simplified details"
        return base + ", slightly calmer and more refined, soft mature storybook quality"

    def _get_age_appearance_hint(self, birth_date_str: str | None) -> str:
        age_months = self._get_pet_age_months(birth_date_str)
        if age_months is None:
            return ""
        if age_months <= 11:
            return "small compact puppy body, playful bouncy pose, curious excited energy, innocent baby-like expression"
        if age_months <= 35:
            return "lively energetic posture, youthful active movement, bright curious expression, lean athletic build"
        if age_months <= 71:
            return "calm composed posture, fully grown adult-sized body, relaxed confident stance, gentle mature expression"
        return (
            "clearly a fully grown adult dog — NOT a puppy, do NOT draw as small or young, "
            "heavier and fuller body shape typical of an older dog, "
            "slow calm relaxed posture, peaceful dignified expression, gentle wise mood, "
            "muzzle and eyebrows may show faint grey or white hairs — visible signs of seniority even in small breeds"
        )

    def _detect_time_of_day(self, texts: list[str]) -> str:
        full = " ".join(texts)
        return "night" if any(kw in full for kw in self.NIGHT_KEYWORDS) else "day"

    def _detect_overseas(self, answers: list[str]) -> str | None:
        full_text = " ".join(answers)
        for kw in self.OVERSEAS_KEYWORDS:
            if kw in full_text:
                return kw
        return None

    def _infer_scene_hint(self, conversation_summary: str) -> str:
        text = conversation_summary or ""
        if any(kw in text for kw in ["동물병원", "병원", "수의사", "검진", "진료", "주사"]):
            return "Scene: inside a warm veterinary clinic — examination table or cozy waiting area, calm and clinical but gentle atmosphere."
        if any(kw in text for kw in ["바다", "해변", "파도", "모래", "부산"]):
            return "Scene: dog at the seaside — shallow waves, beach, sea breeze, curious reaction."
        if any(kw in text for kw in ["공원", "잔디", "풀", "산책", "벚꽃"]):
            return "Scene: dog outdoors in park or on a walk — grass, breeze, movement and interest."
        if any(kw in text for kw in ["소파", "집", "거실", "기대", "옆에", "안겨", "무릎"]):
            return "Scene: cozy indoor moment — dog near the guardian, closeness and emotional bonding."
        if any(kw in text for kw in ["카페", "여행", "기차", "전철", "버스", "외출"]):
            return "Scene: special outing or travel — environmental storytelling, memorable calm atmosphere."
        return "Scene: the most vivid emotional moment from the diary — dog's action, mood, and surroundings."

    def _get_fur_color_rule(self, breed: str, image_prompt_base: str, all_answers: list[str]) -> str:
        text = " ".join([breed or "", image_prompt_base or "", *all_answers]).lower()
        white_keywords = [
            "white", "ivory", "cream", "bichon", "maltese", "spitz", "samoyed",
            "비숑", "말티즈", "스피츠", "사모예드", "흰", "하얀", "백색",
        ]
        if any(kw in text for kw in white_keywords):
            return (
                "fur must remain clearly white, clean neutral white fur, "
                "no yellow or beige fur tint, preserve bright white character readability"
            )
        return "natural fur color, clean readable coat, avoid muddy color cast"

    def _get_breed_en(self, breed: str, breed_en: str | None) -> str:
        if breed_en and breed_en.strip():
            return breed_en.strip()
        return self.BREED_EN_MAP.get(breed, breed)

    def _get_breed_visual_hint(self, breed_en: str) -> str:
        return self.BREED_VISUAL_HINTS.get(breed_en, "")