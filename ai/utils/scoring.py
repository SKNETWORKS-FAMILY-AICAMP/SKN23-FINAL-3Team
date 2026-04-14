# ai/utils/scoring.py
# 반려견 / 보호자 성향 태그 → 타입 분류 + 점수 계산

# ── 반려견 태그 점수표 ─────────────────────────────────────────
# a=활동성, b=사회성, c=안정성, d=탐색성, e=자극민감도
DOG_TAG_SCORES = {
    "에너자이저":           {"a": 5,  "b": 2,  "c": 0,  "d": 2,  "e": -1},
    "느긋한 편":            {"a": 1,  "b": 0,  "c": 2,  "d": 0,  "e": 1},
    "애교쟁이":             {"a": 2,  "b": 3,  "c": 1,  "d": 0,  "e": 0},
    "제 갈 길 가는 타입":   {"a": 1,  "b": -2, "c": 2,  "d": 2,  "e": 0},
    "낯을 가려요":          {"a": -1, "b": -3, "c": -2, "d": 0,  "e": 3},
    "낯선 사람도 좋아요":   {"a": 0,  "b": 4,  "c": 1,  "d": 1,  "e": -1},
    "사람이라면 다 좋아":   {"a": 0,  "b": 5,  "c": 2,  "d": 1,  "e": -1},
    "사람은 좀 무서워요":   {"a": 0,  "b": -4, "c": -1, "d": 0,  "e": 2},
    "겁쟁이":               {"a": -2, "b": -2, "c": -4, "d": -2, "e": 5},
    "겁 없는 탐험가":       {"a": 3,  "b": 1,  "c": 3,  "d": 2,  "e": -2},
    "호기심 폭발":          {"a": 3,  "b": 0,  "c": -1, "d": 5,  "e": -1},
    "고집 있는 편":         {"a": 1,  "b": -1, "c": 0,  "d": 2,  "e": 1},
    "예민한 편":            {"a": 0,  "b": -2, "c": -3, "d": 0,  "e": 5},
    "먹는 게 최고":         {"a": 1,  "b": 1,  "c": 1,  "d": 1,  "e": 0},
    "낯선 것엔 짖어요":     {"a": 1,  "b": -1, "c": -2, "d": 0,  "e": 3},
    "산책이 제일 좋아":     {"a": 4,  "b": 0,  "c": 1,  "d": 3,  "e": -1},
    "밖이 좋아요":          {"a": 3,  "b": 0,  "c": 1,  "d": 3,  "e": -1},
    "집이 편해요":          {"a": -2, "b": 0,  "c": 2,  "d": -1, "e": 2},
    "장난감 수집가":        {"a": 3,  "b": 0,  "c": 1,  "d": 2,  "e": 0},
    "공이라면 뭐든지":      {"a": 4,  "b": 1,  "c": 0,  "d": 1,  "e": -1},
    "강아지 친구 환영":     {"a": 2,  "b": 4,  "c": 1,  "d": 1,  "e": -1},
    "혼자도 잘 놀아요":     {"a": -1, "b": -2, "c": 3,  "d": 0,  "e": -1},
    "안기는 거 좋아요":     {"a": 0,  "b": 3,  "c": 3,  "d": 0,  "e": -1},
    "시키는 건 다 해요":    {"a": 1,  "b": 2,  "c": 2,  "d": 1,  "e": -1},
}

# ── 보호자 태그 점수표 ─────────────────────────────────────────
# a=자연친화성, b=활동에너지, c=사람에너지, d=감성지수, e=실용성
OWNER_TAG_SCORES = {
    "신나게 뛰어놀기":    {"a": 1,  "b": 5,  "c": 0,  "d": 0,  "e": 1},
    "느긋하게 쉬어가기":  {"a": 2,  "b": -2, "c": 0,  "d": 3,  "e": 0},
    "자연 속으로":        {"a": 5,  "b": 1,  "c": -1, "d": 2,  "e": 0},
    "도시 구경":          {"a": -2, "b": 1,  "c": 3,  "d": 1,  "e": 2},
    "일상 충전":          {"a": 1,  "b": -1, "c": 0,  "d": 0,  "e": 1},
    "새로운 곳 구경":     {"a": 0,  "b": 2,  "c": 2,  "d": 1,  "e": 2},
    "감성 충만":          {"a": 1,  "b": -1, "c": 1,  "d": 5,  "e": -1},
    "동네 골목 탐방":     {"a": 1,  "b": 1,  "c": 2,  "d": 2,  "e": 1},
    "계획 없이 떠나기":   {"a": 1,  "b": 2,  "c": 1,  "d": 2,  "e": -1},
    "바다":               {"a": 5,  "b": 2,  "c": 0,  "d": 3,  "e": 0},
    "산":                 {"a": 5,  "b": 4,  "c": 0,  "d": 2,  "e": 0},
    "숲":                 {"a": 5,  "b": 2,  "c": 0,  "d": 3,  "e": 0},
    "계곡":               {"a": 5,  "b": 3,  "c": 0,  "d": 2,  "e": 0},
    "공원 산책":          {"a": 3,  "b": 2,  "c": 2,  "d": 1,  "e": 1},
    "카페 투어":          {"a": -1, "b": 0,  "c": 4,  "d": 3,  "e": 1},
    "핫플 인증":          {"a": -2, "b": 1,  "c": 5,  "d": 4,  "e": 2},
    "사진 건지러":        {"a": 1,  "b": 1,  "c": 2,  "d": 5,  "e": 0},
    "맛있는 거 먹으러":   {"a": -1, "b": 0,  "c": 2,  "d": 1,  "e": 3},
    "전시 관람":          {"a": -1, "b": 1,  "c": 1,  "d": 3,  "e": 1},
}

# ── 반려견 타입 ID ─────────────────────────────────────────────
DOG_TYPES = {
    "d_a": "🐾 산책 탐험대",
    "d_b": "🌼 모두의 단짝",
    "d_c": "🌙 조심스러운 아이",
    "d_d": "🍂 자유로운 영혼",
}

# ── 보호자 타입 ID ─────────────────────────────────────────────
OWNER_TYPES = {
    "o_a": "🌿 자연 애호가",
    "o_b": "✨ 도시 감성러",
    "o_c": "🏃 활발한 활동가",
    "o_d": "🛋️ 느긋한 휴식러",
}


def classify_dog_type(tags: list) -> str:
    """
    반려견 태그 → 반려견 타입 분류

    Parameters:
        tags: 반려견 성격 태그 목록 (최대 5개)
            예: ["에너자이저", "산책이 제일 좋아", "강아지 친구 환영"]

    Returns:
        타입 ID (예: "d_a")
        - d_a: 🐾 산책 탐험대 (활동성·탐색성 높음)
        - d_b: 🌼 모두의 단짝 (사회성 높음)
        - d_c: 🌙 조심스러운 아이 (자극민감도 높음) ← 동점 시 우선
        - d_d: 🍂 자유로운 영혼 (안정성·독립성 높음)
    """
    scores = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}

    for tag in tags:
        if tag not in DOG_TAG_SCORES:
            print(f"알 수 없는 반려견 태그: {tag}")
            continue
        for axis, value in DOG_TAG_SCORES[tag].items():
            scores[axis] += value

    # 타입 결정
    if scores["a"] >= scores["b"] and scores["d"] >= scores["b"]:
        return "d_a"  # 🐾 산책 탐험대
    elif scores["b"] == max(scores.values()):
        return "d_b"  # 🌼 모두의 단짝
    elif scores["e"] == max(scores.values()):
        return "d_c"  # 🌙 조심스러운 아이
    else:
        return "d_d"  # 🍂 자유로운 영혼


def classify_owner_type(tags: list) -> str:
    """
    보호자 태그 → 보호자 타입 분류

    Parameters:
        tags: 보호자 라이프스타일 태그 목록 (최대 5개)
            예: ["자연 속으로", "공원 산책", "사진 건지러"]

    Returns:
        타입 ID (예: "o_a")
        - o_a: 🌿 자연 애호가 (자연친화성 높음)
        - o_b: ✨ 도시 감성러 (감성·사람에너지 높음)
        - o_c: 🏃 활발한 활동가 (활동에너지 높음)
        - o_d: 🛋️ 느긋한 휴식러 (감성·실용성 높음) ← 동점 시 우선
    """
    scores = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}

    for tag in tags:
        if tag not in OWNER_TAG_SCORES:
            print(f"알 수 없는 보호자 태그: {tag}")
            continue
        for axis, value in OWNER_TAG_SCORES[tag].items():
            scores[axis] += value

    # 타입 결정
    if scores["a"] == max(scores.values()):
        return "o_a"  # 🌿 자연 애호가
    elif scores["d"] >= scores["b"] and scores["c"] >= scores["b"]:
        return "o_b"  # ✨ 도시 감성러
    elif scores["b"] == max(scores.values()):
        return "o_c"  # 🏃 활발한 활동가
    else:
        return "o_d"  # 🛋️ 느긋한 휴식러


def calculate_dog_score_vector(tags: list) -> dict:
    """
    반려견 태그 → 점수 벡터 반환
    → ChromaDB 검색 후 재순위(reranking)에 활용

    Parameters:
        tags: 반려견 성격 태그 목록

    Returns:
        {"a": 8, "b": 6, "c": 0, "d": 5, "e": -2}
    """
    scores = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}
    for tag in tags:
        if tag not in DOG_TAG_SCORES:
            continue
        for axis, value in DOG_TAG_SCORES[tag].items():
            scores[axis] += value
    return scores


def calculate_owner_score_vector(tags: list) -> dict:
    """
    보호자 태그 → 점수 벡터 반환
    → ChromaDB 검색 쿼리 생성에 활용

    Parameters:
        tags: 보호자 라이프스타일 태그 목록

    Returns:
        {"a": 10, "b": 3, "c": -1, "d": 5, "e": 0}
    """
    scores = {"a": 0, "b": 0, "c": 0, "d": 0, "e": 0}
    for tag in tags:
        if tag not in OWNER_TAG_SCORES:
            continue
        for axis, value in OWNER_TAG_SCORES[tag].items():
            scores[axis] += value
    return scores


def get_type_name(type_id: str) -> str:
    """
    타입 ID → 타입 이름 반환

    Parameters:
        type_id: "d_a" 또는 "o_a"

    Returns:
        "🐾 산책 탐험대"
    """
    return DOG_TYPES.get(type_id) or OWNER_TYPES.get(type_id, "알 수 없는 타입")