import logging
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import DEFAULT_OUTPUT_DIR

logger = logging.getLogger(__name__)


def save_results(records: list[dict], output_path: str = None, run_id: str = None) -> Path:
    """평가 결과를 새 엑셀 파일로 저장. 원본 파일은 수정하지 않는다."""
    if output_path:
        out = Path(output_path)
    else:
        ts = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        out = DEFAULT_OUTPUT_DIR / f"eval_results_{ts}.xlsx"

    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for r in records:
        tops = r.get("top_results", [])
        row = {
            "run_id": r.get("run_id", ""),
            "query_id": r.get("query_id", ""),
            "카테고리": r.get("category", ""),
            "사용자질문": r.get("question", ""),
            "정답": ", ".join(r.get("answers", [])),
            "top1": tops[0] if len(tops) > 0 else "",
            "top2": tops[1] if len(tops) > 1 else "",
            "top3": tops[2] if len(tops) > 2 else "",
            "top4": tops[3] if len(tops) > 3 else "",
            "top5": tops[4] if len(tops) > 4 else "",
            "hit_at_5": r.get("hit_at_5", ""),
            "recall_at_5": r.get("recall_at_5", ""),
            "refusal": r.get("refusal", ""),
            "비고": f"ERROR: {r['error']}" if r.get("error") else r.get("note", ""),
        }
        rows.append(row)

    pd.DataFrame(rows).to_excel(out, index=False)
    logger.info("Results saved → %s", out)
    return out
