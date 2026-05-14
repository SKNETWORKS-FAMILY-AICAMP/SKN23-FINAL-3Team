# -*- coding: utf-8 -*-
"""
Trait-aware place recommendation evaluation.

This script evaluates whether dog/owner trait profiles affect place ranking in
the expected direction. It reads the trait evaluation workbook, calls the eval
place-search endpoint with row-level dog_tags/owner_tags, and writes row-level
metrics plus summary sheets.
"""

from __future__ import annotations

import argparse
import math
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))

from api_client import parse_query_eval, search_places_eval_with_profile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATASET = Path("data/eval/성향 점수 평가셋_50문항.xlsx")
DEFAULT_OUTPUT_DIR = Path("ai/evaluation/results")
TOP_K = 5


def _resolve_path(path: str | Path) -> Path:
    resolved = Path(path)
    if not resolved.is_absolute():
        resolved = PROJECT_ROOT / resolved
    return resolved


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except TypeError:
        return False


def _text(value: Any) -> str:
    if _is_blank(value):
        return ""
    return str(value).strip()


def _row_value(row: pd.Series, *columns: str) -> Any:
    for column in columns:
        if column in row and not _is_blank(row.get(column)):
            return row.get(column)
    return ""


def _normalize(value: Any) -> str:
    return re.sub(r"[\s\W_]+", "", _text(value)).lower()


def _split_multi_value(value: Any) -> list[str]:
    text = _text(value)
    if not text:
        return []

    cleaned = text.replace("\r", "\n")
    cleaned = re.sub(r"\btop\s*\d+\s*[:.)-]?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\s*\d+\s*[.)-]\s*", "", cleaned, flags=re.MULTILINE)

    parts = re.split(r"[;\n|]+", cleaned)
    if len(parts) == 1 and "," in cleaned:
        parts = cleaned.split(",")

    return [part.strip() for part in parts if part.strip()]


def _matches(left: str, right: str) -> bool:
    left_norm = _normalize(left)
    right_norm = _normalize(right)
    return bool(left_norm and right_norm and (left_norm in right_norm or right_norm in left_norm))


def _parse_profile_tags(tag_or_tags: Any, profile_category: Any = "") -> tuple[list[str], list[str]]:
    text = _text(tag_or_tags)
    profile = _text(profile_category).upper()
    if not text:
        return [], []

    dog_match = re.search(r"dog\s*=\s*(.*?)(?:/|owner\s*=|$)", text, flags=re.IGNORECASE)
    owner_match = re.search(r"owner\s*=\s*(.*)$", text, flags=re.IGNORECASE)

    dog_tags = _split_multi_value(dog_match.group(1)) if dog_match else []
    owner_tags = _split_multi_value(owner_match.group(1)) if owner_match else []

    if not dog_tags and not owner_tags:
        tags = _split_multi_value(text)
        if profile == "OWNER_ONLY":
            owner_tags = tags
        else:
            dog_tags = tags

    return dog_tags, owner_tags


def _place_name(place: dict) -> str:
    return _text(place.get("name"))


def _place_category(place: dict) -> str:
    category = _text(place.get("category"))
    sub_category = _text(place.get("sub_category"))
    values = [value for value in (category, sub_category) if value]
    return ";".join(dict.fromkeys(values))


def _category_matches(place: dict, expected_categories: list[str]) -> bool:
    if not expected_categories:
        return False
    tokens = [_place_category(place), place.get("category", ""), place.get("sub_category", "")]
    for expected in expected_categories:
        if any(_matches(expected, token) for token in tokens):
            return True
    return False


def calc_hit_at_k(answers: list[str], results: list[str], k: int = TOP_K) -> float:
    top_results = results[:k]
    return 1.0 if any(any(_matches(answer, result) for result in top_results) for answer in answers) else 0.0


def calc_recall_at_k(answers: list[str], results: list[str], k: int = TOP_K) -> float:
    if not answers:
        return 0.0
    top_results = results[:k]
    matched = sum(1 for answer in answers if any(_matches(answer, result) for result in top_results))
    return round(matched / len(answers), 4)


def calc_ndcg_at_k(answers: list[str], results: list[str], k: int = TOP_K) -> float:
    if not answers:
        return 0.0

    relevance_by_answer = {
        answer: len(answers) - idx
        for idx, answer in enumerate(answers)
    }

    dcg = 0.0
    used_answers: set[str] = set()
    for rank, result in enumerate(results[:k], start=1):
        relevance = 0.0
        matched_answer = ""
        for answer, answer_relevance in relevance_by_answer.items():
            if answer in used_answers:
                continue
            if _matches(answer, result):
                relevance = float(answer_relevance)
                matched_answer = answer
                break
        if matched_answer:
            used_answers.add(matched_answer)
        dcg += relevance / math.log2(rank + 1)

    ideal_relevance = sorted(relevance_by_answer.values(), reverse=True)[:k]
    idcg = sum(rel / math.log2(rank + 1) for rank, rel in enumerate(ideal_relevance, start=1))
    return round(dcg / idcg, 4) if idcg else 0.0


def _evaluate_row(row: pd.Series, n_results: int, mode: str, parsed: dict | None = None) -> dict:
    query = _text(_row_value(row, "사용자 질문", "사용자질문"))
    profile_category = _text(row.get("profile_category"))
    dog_tags, owner_tags = _parse_profile_tags(row.get("tag_or_tags"), profile_category)

    answers = _split_multi_value(_row_value(row, "정답", "정답 장소 Top 5"))
    preferred_categories = _split_multi_value(row.get("preferred_categories"))
    avoid_categories = _split_multi_value(row.get("avoid_categories"))

    places = search_places_eval_with_profile(
        query=query,
        dog_tags=dog_tags,
        owner_tags=owner_tags,
        n_results=n_results,
        mode=mode,
        parsed=parsed,
    )
    top_places = places[:TOP_K]
    top_names = [_place_name(place) for place in top_places]
    top_categories = [_place_category(place) for place in top_places]

    preferred_hit_count = sum(1 for place in top_places if _category_matches(place, preferred_categories))
    avoid_violation_count = sum(1 for place in top_places if _category_matches(place, avoid_categories))
    returned_count = len(top_places)

    result = {
        "dog_tags_used": ";".join(dog_tags),
        "owner_tags_used": ";".join(owner_tags),
        "answer_count": len(answers),
        "returned_count": returned_count,
        "hit_at_5": calc_hit_at_k(answers, top_names),
        "recall_at_5": calc_recall_at_k(answers, top_names),
        "ndcg_at_5": calc_ndcg_at_k(answers, top_names),
        "preferred_category_hit_count": preferred_hit_count,
        "preferred_category_rate": round(preferred_hit_count / returned_count, 4) if returned_count else 0.0,
        "avoid_category_violation_count": avoid_violation_count,
        "avoid_category_violation_rate": round(avoid_violation_count / returned_count, 4) if returned_count else 0.0,
        "category_pass": 1.0 if preferred_hit_count > 0 and avoid_violation_count == 0 else 0.0,
        "top_results": ";".join(top_names),
        "top_result_categories": ";".join(top_categories),
        "error": "",
    }

    for idx in range(TOP_K):
        place = top_places[idx] if idx < len(top_places) else {}
        result[f"top{idx + 1}_name"] = _place_name(place)
        result[f"top{idx + 1}_category"] = _place_category(place)
        result[f"top{idx + 1}_score"] = place.get("final_score", "")

    return result


def _mean(series: pd.Series) -> float:
    values = pd.to_numeric(series, errors="coerce").dropna()
    return round(float(values.mean()), 4) if not values.empty else 0.0


def _summary(df: pd.DataFrame, group_cols: list[str] | None = None) -> pd.DataFrame:
    metric_cols = [
        "hit_at_5",
        "recall_at_5",
        "ndcg_at_5",
        "preferred_category_rate",
        "avoid_category_violation_rate",
        "category_pass",
    ]
    valid = df[df["error"].fillna("") == ""].copy()

    if group_cols:
        rows = []
        for keys, group in valid.groupby(group_cols, dropna=False):
            if not isinstance(keys, tuple):
                keys = (keys,)
            row = {col: key for col, key in zip(group_cols, keys)}
            row["row_count"] = len(group)
            for metric in metric_cols:
                row[f"avg_{metric}"] = _mean(group[metric])
            rows.append(row)
        return pd.DataFrame(rows)

    row = {
        "row_count": len(df),
        "evaluated_count": len(valid),
        "error_count": len(df) - len(valid),
    }
    for metric in metric_cols:
        row[f"avg_{metric}"] = _mean(valid[metric])
    return pd.DataFrame([row])


def _save_evaluation_workbook(evaluated: pd.DataFrame, output_path: Path) -> None:
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        evaluated.to_excel(writer, sheet_name="details", index=False)
        _summary(evaluated).to_excel(writer, sheet_name="summary_overall", index=False)
        _summary(evaluated, ["profile_category"]).to_excel(
            writer,
            sheet_name="summary_by_profile",
            index=False,
        )
        _summary(evaluated, ["expected_type"]).to_excel(
            writer,
            sheet_name="summary_by_type",
            index=False,
        )
        question_col = "사용자 질문" if "사용자 질문" in evaluated.columns else "사용자질문"
        _summary(evaluated, [question_col]).to_excel(
            writer,
            sheet_name="summary_by_question",
            index=False,
        )


def print_summary(df: pd.DataFrame) -> None:
    overall = _summary(df).iloc[0].to_dict()
    print("\n" + "=" * 64)
    print("성향 기반 장소추천 평가 결과 요약")
    print("=" * 64)
    print(f"전체 row 수       : {int(overall['row_count'])}")
    print(f"평가 완료 row 수  : {int(overall['evaluated_count'])}")
    print(f"오류 row 수       : {int(overall['error_count'])}")
    print(f"평균 Hit@5        : {overall['avg_hit_at_5']:.4f}")
    print(f"평균 Recall@5     : {overall['avg_recall_at_5']:.4f}")
    print(f"평균 NDCG@5       : {overall['avg_ndcg_at_5']:.4f}")
    print(f"선호 카테고리 비율: {overall['avg_preferred_category_rate']:.4f}")
    print(f"회피 카테고리 비율: {overall['avg_avoid_category_violation_rate']:.4f}")
    print(f"카테고리 통과율   : {overall['avg_category_pass']:.4f}")
    print("=" * 64)


def _default_output(round_no: int | None) -> Path:
    suffix = f"round{round_no}" if round_no is not None else datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_OUTPUT_DIR / f"성향 점수 평가셋_50문항_{suffix}.xlsx"


def run(
    dataset: str | Path = DEFAULT_DATASET,
    output: str | Path | None = None,
    round_no: int | None = None,
    limit: int | None = None,
    n_results: int = 20,
    mode: str = "combined",
    use_parse_cache: bool = True,
    checkpoint_every: int = 250,
) -> Path:
    dataset_path = _resolve_path(dataset)
    if not dataset_path.exists():
        raise FileNotFoundError(f"평가셋 파일을 찾을 수 없습니다: {dataset_path}")

    output_path = _resolve_path(output or _default_output(round_no))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_excel(dataset_path)
    answer_col = "정답" if "정답" in df.columns else "정답 장소 Top 5"
    before_filter_count = len(df)
    df = df[df[answer_col].apply(lambda value: bool(_split_multi_value(value)))].copy()
    removed_count = before_filter_count - len(df)
    if removed_count:
        print(f"정답이 비어 있는 row {removed_count}개를 평가에서 제외했습니다.")

    if limit is not None:
        df = df.head(limit).copy()

    records = []
    parse_cache: dict[str, dict | None] = {}
    total = len(df)
    for idx, row in df.iterrows():
        display_idx = len(records) + 1
        if display_idx == 1 or display_idx % 50 == 0 or display_idx == total:
            print(f"[{display_idx}/{total}] 평가 중...")

        base_record = row.to_dict()
        base_record["round"] = round_no if round_no is not None else ""
        try:
            query = _text(_row_value(row, "사용자 질문", "사용자질문"))
            parsed = None
            if use_parse_cache:
                if query not in parse_cache:
                    parse_cache[query] = parse_query_eval(query)
                parsed = parse_cache[query]

            eval_result = _evaluate_row(
                row,
                n_results=n_results,
                mode=mode,
                parsed=parsed,
            )
            records.append({**base_record, **eval_result})
        except Exception as exc:
            error_record = {
                "dog_tags_used": "",
                "owner_tags_used": "",
                "answer_count": len(_split_multi_value(_row_value(row, "정답", "정답 장소 Top 5"))),
                "returned_count": 0,
                "hit_at_5": 0.0,
                "recall_at_5": 0.0,
                "ndcg_at_5": 0.0,
                "preferred_category_hit_count": 0,
                "preferred_category_rate": 0.0,
                "avoid_category_violation_count": 0,
                "avoid_category_violation_rate": 0.0,
                "category_pass": 0.0,
                "top_results": "",
                "top_result_categories": "",
                "error": str(exc),
            }
            for top_idx in range(TOP_K):
                error_record[f"top{top_idx + 1}_name"] = ""
                error_record[f"top{top_idx + 1}_category"] = ""
                error_record[f"top{top_idx + 1}_score"] = ""
            records.append({**base_record, **error_record})

        if checkpoint_every and len(records) % checkpoint_every == 0:
            checkpoint_path = output_path.with_name(f"{output_path.stem}_checkpoint.xlsx")
            _save_evaluation_workbook(pd.DataFrame(records), checkpoint_path)
            print(f"체크포인트 저장: {checkpoint_path}")

    evaluated = pd.DataFrame(records)
    _save_evaluation_workbook(evaluated, output_path)

    print_summary(evaluated)
    print(f"\n결과 파일: {output_path}")
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="withDOG 성향 기반 장소추천 평가")
    parser.add_argument(
        "--dataset",
        default=str(DEFAULT_DATASET),
        help='입력 평가셋 경로. 기본값: "data/eval/성향 점수 평가셋_50문항.xlsx"',
    )
    parser.add_argument(
        "--output",
        help="결과 저장 경로. 생략하면 ai/evaluation/results 아래에 round 기준 파일명으로 저장합니다.",
    )
    parser.add_argument("--round", type=int, help="반복 평가 차수 라벨. 예: --round 1")
    parser.add_argument("--limit", type=int, help="처음 N개 row만 실행합니다. 테스트용입니다.")
    parser.add_argument("--n-results", type=int, default=20, help="후보 검색 개수. 기본값: 20")
    parser.add_argument("--mode", default="combined", choices=("combined", "rdb_only", "rag_only"))
    parser.add_argument(
        "--no-parse-cache",
        action="store_true",
        help="질문 파싱 결과 캐시를 사용하지 않습니다.",
    )
    parser.add_argument(
        "--checkpoint-every",
        type=int,
        default=250,
        help="N개 row마다 checkpoint 엑셀을 저장합니다. 0이면 비활성화합니다.",
    )
    args = parser.parse_args()

    run(
        dataset=args.dataset,
        output=args.output,
        round_no=args.round,
        limit=args.limit,
        n_results=args.n_results,
        mode=args.mode,
        use_parse_cache=not args.no_parse_cache,
        checkpoint_every=args.checkpoint_every,
    )


if __name__ == "__main__":
    main()
