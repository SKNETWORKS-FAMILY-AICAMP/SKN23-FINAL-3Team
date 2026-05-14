import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import DEFAULT_OUTPUT_DIR

OPTIMIZATION_LOG_PATH = DEFAULT_OUTPUT_DIR / "optimization_log.xlsx"

logger = logging.getLogger(__name__)

MODE_LABELS = {
    "combined": "Combined",
    "rdb_only": "RDB only",
    "rag_only": "RAG only",
}
MODE_ORDER = ["combined", "rdb_only", "rag_only"]
REPORT_K_VALUES = [1, 3, 5, 10, 20]


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
        row["parsed_objective"] = r.get("parsed_objective", "")
        row["parsed_subjective"] = r.get("parsed_subjective", "")
        row["time_condition"] = r.get("time_condition", "")
        row["use_current_location"] = r.get("use_current_location", "")
        row["landmark"] = r.get("landmark", "")
        row["landmark_coords"] = r.get("landmark_coords", "")
        row["rdb_candidate_count"] = r.get("rdb_candidate_count", "")
        row["answer_in_rdb_candidates"] = r.get("answer_in_rdb_candidates", "")
        row["answer_candidate_rank"] = r.get("answer_candidate_rank", "")
        row["answer_rank_rdb"] = r.get("answer_rank_rdb", "")
        row["failure_type"] = r.get("failure_type", "")
        row["rdb_debug_top_names"] = r.get("rdb_debug_top_names", "")
        row["diagnostic_error"] = r.get("diagnostic_error", "")
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
        _write_report_sheet(writer, df_summary, df_by_cat)

    logger.info("Ablation results saved → %s", out)

    _append_optimization_log(df_summary, run_id)

    return out


def _write_report_sheet(
    writer: pd.ExcelWriter,
    df_summary: pd.DataFrame,
    df_by_cat: pd.DataFrame,
) -> None:
    """발표/보고서에 바로 옮기기 쉬운 요약 시트를 추가한다."""
    sheet_name = "report"
    start_row = 0

    start_row = _write_titled_table(
        writer,
        sheet_name,
        "전체 지표 - Hit@k",
        _build_overall_report(df_summary, "hit_rate", "Hit"),
        start_row,
    )
    start_row = _write_titled_table(
        writer,
        sheet_name,
        "전체 지표 - Recall@k",
        _build_overall_report(df_summary, "recall_rate", "Recall"),
        start_row + 1,
    )
    category_report = _build_category_report(df_by_cat)
    start_row = _write_titled_table(
        writer,
        sheet_name,
        "카테고리별 결과 (Combined, k=5)",
        category_report,
        start_row + 1,
    )
    _write_titled_table(
        writer,
        sheet_name,
        "강점/약점 요약",
        _build_strength_weakness_report(category_report),
        start_row + 1,
    )

    _format_report_sheet(writer, sheet_name)


def _build_overall_report(
    df_summary: pd.DataFrame,
    metric_col: str,
    metric_label: str,
) -> pd.DataFrame:
    if df_summary.empty:
        return pd.DataFrame(columns=["모드", *[f"{metric_label}@{k}" for k in REPORT_K_VALUES]])

    pivot = df_summary.pivot_table(index="mode", columns="k", values=metric_col, aggfunc="first")
    rows = []
    for mode in MODE_ORDER:
        if mode not in pivot.index:
            continue
        row = {"모드": MODE_LABELS.get(mode, mode)}
        for k in REPORT_K_VALUES:
            row[f"{metric_label}@{k}"] = pivot.loc[mode, k] if k in pivot.columns else ""
        rows.append(row)
    return pd.DataFrame(rows)


def _build_category_report(df_by_cat: pd.DataFrame) -> pd.DataFrame:
    columns = ["카테고리", "n", "Hit@5", "Recall@5"]
    if df_by_cat.empty:
        return pd.DataFrame(columns=columns)

    sub = df_by_cat[(df_by_cat["mode"] == "combined") & (df_by_cat["k"] == 5)].copy()
    if sub.empty:
        return pd.DataFrame(columns=columns)

    sub = sub.rename(columns={"hit_rate": "Hit@5", "recall_rate": "Recall@5"})
    sub = sub[columns].sort_values(["Hit@5", "Recall@5", "카테고리"], ascending=[False, False, True])
    return sub.reset_index(drop=True)


def _build_strength_weakness_report(category_report: pd.DataFrame) -> pd.DataFrame:
    columns = ["구분", "카테고리", "기준", "해석"]
    if category_report.empty:
        return pd.DataFrame(columns=columns)

    ranked = category_report[category_report["Hit@5"] != ""].copy()
    if ranked.empty:
        return pd.DataFrame(columns=columns)

    weak = ranked.sort_values(["Hit@5", "Recall@5", "카테고리"], ascending=[True, True, True]).head(3)
    strong = ranked.sort_values(["Hit@5", "Recall@5", "카테고리"], ascending=[False, False, True]).head(3)

    rows = [
        {
            "구분": "약점",
            "카테고리": ", ".join(weak["카테고리"].tolist()),
            "기준": "Combined Hit@5 하위 3개",
            "해석": "필터 조건 기반 쿼리 또는 복합 조건에서 보완 필요",
        },
        {
            "구분": "강점",
            "카테고리": ", ".join(strong["카테고리"].tolist()),
            "기준": "Combined Hit@5 상위 3개",
            "해석": "명시적 조건 쿼리에서 상대적으로 안정적",
        },
    ]
    return pd.DataFrame(rows, columns=columns)


def _write_titled_table(
    writer: pd.ExcelWriter,
    sheet_name: str,
    title: str,
    df: pd.DataFrame,
    start_row: int,
) -> int:
    workbook = writer.book
    if sheet_name in writer.sheets:
        worksheet = writer.sheets[sheet_name]
    else:
        worksheet = workbook.create_sheet(sheet_name)
        writer.sheets[sheet_name] = worksheet

    worksheet.cell(row=start_row + 1, column=1, value=title)
    df.to_excel(writer, sheet_name=sheet_name, startrow=start_row + 1, index=False)
    return start_row + len(df) + 3


def _format_report_sheet(writer: pd.ExcelWriter, sheet_name: str) -> None:
    worksheet = writer.sheets[sheet_name]
    for row in worksheet.iter_rows():
        for cell in row:
            if cell.value is None:
                continue
            if isinstance(cell.value, float):
                cell.number_format = "0.0%"

    for column_cells in worksheet.columns:
        max_len = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_len + 2, 10), 45)


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
