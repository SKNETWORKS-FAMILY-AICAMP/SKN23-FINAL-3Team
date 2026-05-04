import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import DEFAULT_OUTPUT_DIR

OPTIMIZATION_LOG_PATH = DEFAULT_OUTPUT_DIR / "optimization_log.xlsx"

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


def save_ablation_results(records: list[dict], output_path: str = None, run_id: str = None) -> Path:
    """Ablation 평가 결과를 멀티시트 엑셀로 저장.

    Sheets:
        raw         — 질문별 전체 결과 (mode × k × query)
        summary     — mode × k 별 Hit/Recall 집계
        by_category — mode × k × 카테고리 별 집계
    """
    if output_path:
        out = Path(output_path)
    else:
        ts = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        out = DEFAULT_OUTPUT_DIR / f"ablation_{ts}.xlsx"

    out.parent.mkdir(parents=True, exist_ok=True)

    max_k = 20

    # raw sheet
    raw_rows = []
    for r in records:
        tops = r.get("top_results", [])
        row = {
            "run_id": r.get("run_id", ""),
            "mode": r.get("mode", ""),
            "k": r.get("k", ""),
            "query_id": r.get("query_id", ""),
            "카테고리": r.get("category", ""),
            "사용자질문": r.get("question", ""),
            "정답": ", ".join(r.get("answers", [])),
        }
        for i in range(1, max_k + 1):
            row[f"top{i}"] = tops[i - 1] if len(tops) >= i else ""
        row["hit_at_k"] = r.get("hit_at_k", "")
        row["recall_at_k"] = r.get("recall_at_k", "")
        row["비고"] = f"ERROR: {r['error']}" if r.get("error") else ""
        raw_rows.append(row)

    df_raw = pd.DataFrame(raw_rows)

    retrieval = [
        r for r in records
        if r.get("eval_type") == "retrieval"
        and not r.get("error")
        and r.get("hit_at_k") != ""
    ]

    # summary sheet
    by_mode_k: dict = defaultdict(list)
    for r in retrieval:
        by_mode_k[(r["mode"], r["k"])].append(r)

    summary_rows = []
    for (mode, k), items in sorted(by_mode_k.items(), key=lambda x: (x[0][0], x[0][1])):
        hit = sum(i["hit_at_k"] for i in items) / len(items)
        recall = sum(i["recall_at_k"] for i in items) / len(items)
        summary_rows.append({
            "mode": mode, "k": k, "n": len(items),
            "hit_rate": round(hit, 4), "recall_rate": round(recall, 4),
        })

    df_summary = pd.DataFrame(summary_rows)

    # by_category sheet
    by_mode_k_cat: dict = defaultdict(list)
    for r in retrieval:
        by_mode_k_cat[(r["mode"], r["k"], r["category"])].append(r)

    cat_rows = []
    for (mode, k, cat), items in sorted(by_mode_k_cat.items()):
        hit = sum(i["hit_at_k"] for i in items) / len(items)
        recall = sum(i["recall_at_k"] for i in items) / len(items)
        cat_rows.append({
            "mode": mode, "k": k, "카테고리": cat, "n": len(items),
            "hit_rate": round(hit, 4), "recall_rate": round(recall, 4),
        })

    df_by_cat = pd.DataFrame(cat_rows)

    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        df_raw.to_excel(writer, sheet_name="raw", index=False)
        df_summary.to_excel(writer, sheet_name="summary", index=False)
        df_by_cat.to_excel(writer, sheet_name="by_category", index=False)

    logger.info("Ablation results saved → %s", out)

    _append_optimization_log(df_summary, run_id)

    return out


def _append_optimization_log(df_summary: pd.DataFrame, run_id: str) -> None:
    """Hit@5 / Recall@5 행을 optimization_log.xlsx 에 누적 append."""
    run_date = datetime.now().strftime("%Y-%m-%d")

    k5 = df_summary[df_summary["k"] == 5][["mode", "hit_rate", "recall_rate"]].copy()
    k5.insert(0, "run_id", run_id)
    k5.insert(1, "실행일", run_date)
    k5.insert(2, "변경 조건", "")
    k5.rename(columns={"hit_rate": "Hit@5", "recall_rate": "Recall@5"}, inplace=True)
    k5["비고"] = ""

    if OPTIMIZATION_LOG_PATH.exists():
        existing = pd.read_excel(OPTIMIZATION_LOG_PATH)
        combined = pd.concat([existing, k5], ignore_index=True)
    else:
        combined = k5

    OPTIMIZATION_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    combined.to_excel(OPTIMIZATION_LOG_PATH, index=False)
    logger.info("Optimization log updated → %s", OPTIMIZATION_LOG_PATH)
