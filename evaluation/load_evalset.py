import logging
from pathlib import Path

import pandas as pd

from config import DEFAULT_EVAL_PATH, EVAL_SHEET_INDEX, REFUSAL_CATEGORY

logger = logging.getLogger(__name__)


def _parse_answers(raw: str) -> list[str]:
    """쉼표로 구분된 정답 문자열을 리스트로 파싱."""
    return [a.strip() for a in str(raw).split(",") if a.strip()]


def _is_empty(value) -> bool:
    if value is None:
        return True
    if pd.isna(value):
        return True
    return str(value).strip() == ""


def load_evalset(path=None) -> list[dict]:
    """엑셀 평가셋을 로드해 평가 항목 리스트로 반환.

    eval_type:
        "retrieval" - Hit@5, Recall@5 계산 대상
        "refusal"   - API 0개 반환이 정답인 케이스
    """
    excel_path = Path(path) if path else DEFAULT_EVAL_PATH
    df = pd.read_excel(excel_path, sheet_name=EVAL_SHEET_INDEX)

    items = []
    skipped = 0

    for _, row in df.iterrows():
        category = row.get("카테고리")
        if _is_empty(category):
            skipped += 1
            continue

        category = str(category).strip()
        question = str(row.get("사용자 질문", "")).strip()
        query_id = str(row.get("query_id", "")).strip()
        note = "" if _is_empty(row.get("비고")) else str(row.get("비고")).strip()
        answer_raw = row.get("정답")

        # 오류/범위 밖 → 전부 Refusal 케이스
        if category == REFUSAL_CATEGORY:
            items.append(
                {
                    "query_id": query_id,
                    "category": category,
                    "question": question,
                    "answers": [],
                    "eval_type": "refusal",
                    "note": note,
                }
            )
            continue

        # 정답 없으면 스킵
        if _is_empty(answer_raw):
            logger.debug("Skip (no answer): query_id=%s", query_id)
            skipped += 1
            continue

        items.append(
            {
                "query_id": query_id,
                "category": category,
                "question": question,
                "answers": _parse_answers(answer_raw),
                "eval_type": "retrieval",
                "note": note,
            }
        )

    retrieval_count = sum(1 for i in items if i["eval_type"] == "retrieval")
    refusal_count = sum(1 for i in items if i["eval_type"] == "refusal")
    logger.info(
        "Loaded %d items (retrieval=%d, refusal=%d, skipped=%d) from %s",
        len(items),
        retrieval_count,
        refusal_count,
        skipped,
        excel_path,
    )
    return items
