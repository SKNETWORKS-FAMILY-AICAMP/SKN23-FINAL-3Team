import re


def _normalize(text: str) -> str:
    """공백·특수문자 제거 후 소문자화."""
    return re.sub(r"[\s\W]", "", text).lower()


def _is_match(answer: str, result: str) -> bool:
    """부분 일치: 정답 ⊂ 결과 또는 결과 ⊂ 정답."""
    a = _normalize(answer)
    r = _normalize(result)
    return bool(a and r and (a in r or r in a))


def calc_hit_at_k(answers: list[str], results: list[str], k: int = 5) -> float:
    """Top-k 결과에 정답이 하나라도 포함되면 1, 아니면 0."""
    top_k = results[:k]
    for answer in answers:
        if any(_is_match(answer, r) for r in top_k):
            return 1.0
    return 0.0


def calc_recall_at_k(answers: list[str], results: list[str], k: int = 5) -> float:
    """Top-k 결과에 포함된 정답 비율."""
    if not answers:
        return 0.0
    top_k = results[:k]
    matched = sum(1 for a in answers if any(_is_match(a, r) for r in top_k))
    return round(matched / len(answers), 4)


def calc_refusal(results: list[str]) -> float:
    """API가 0개 반환 → 1 (올바른 거절), 1개 이상 반환 → 0 (hallucination)."""
    return 1.0 if len(results) == 0 else 0.0
