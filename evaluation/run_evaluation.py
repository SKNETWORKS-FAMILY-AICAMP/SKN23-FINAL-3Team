import argparse
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))

from api_client import search_places
from load_evalset import load_evalset
from metrics import calc_hit_at_k, calc_recall_at_k, calc_refusal
from save_results import save_results

LOG_DIR = Path(__file__).parent / "logs"


def _setup_logging(verbose: bool, run_id: str) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"run_{run_id}.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )
    logging.getLogger(__name__).info("로그 파일: %s", log_file)


def _print_summary(records: list[dict]) -> None:
    retrieval = [r for r in records if r.get("eval_type") == "retrieval" and not r.get("error")]
    refusal = [r for r in records if r.get("eval_type") == "refusal" and not r.get("error")]
    errors = [r for r in records if r.get("error")]

    print("\n" + "=" * 60)
    print("평가 결과 요약")
    print("=" * 60)

    # 전체 지표
    if retrieval:
        overall_hit = sum(r["hit_at_5"] for r in retrieval) / len(retrieval)
        overall_recall = sum(r["recall_at_5"] for r in retrieval) / len(retrieval)
        print(f"\n[전체 Retrieval] n={len(retrieval)}")
        print(f"  Hit@5    : {overall_hit:.4f} ({overall_hit*100:.1f}%)")
        print(f"  Recall@5 : {overall_recall:.4f} ({overall_recall*100:.1f}%)")

    if refusal:
        refusal_rate = sum(r["refusal"] for r in refusal) / len(refusal)
        print(f"\n[전체 Refusal] n={len(refusal)}")
        print(f"  Refusal Rate : {refusal_rate:.4f} ({refusal_rate*100:.1f}%)")

    # 카테고리별
    by_category: dict[str, list] = defaultdict(list)
    for r in records:
        if not r.get("error"):
            by_category[r["category"]].append(r)

    print("\n[카테고리별]")
    print(f"{'카테고리':<20} {'n':>4}  {'Hit@5':>7}  {'Recall@5':>9}  {'Refusal':>8}")
    print("-" * 58)
    for cat, items in sorted(by_category.items()):
        ret = [i for i in items if i["eval_type"] == "retrieval"]
        ref = [i for i in items if i["eval_type"] == "refusal"]
        hit_str = f"{sum(i['hit_at_5'] for i in ret)/len(ret):.3f}" if ret else "-"
        rec_str = f"{sum(i['recall_at_5'] for i in ret)/len(ret):.3f}" if ret else "-"
        ref_str = f"{sum(i['refusal'] for i in ref)/len(ref):.3f}" if ref else "-"
        n = len(items)
        print(f"{cat:<20} {n:>4}  {hit_str:>7}  {rec_str:>9}  {ref_str:>8}")

    if errors:
        print(f"\n[에러] {len(errors)}건 (결과 파일 비고 컬럼 확인)")

    print("=" * 60)


def run(
    input_path: str = None,
    output_path: str = None,
    limit: int = None,
    category: str = None,
    verbose: bool = False,
    run_id: str = None,
) -> list[dict]:
    if run_id is None:
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    items = load_evalset(input_path)

    if category:
        items = [i for i in items if i["category"] == category]
        logging.getLogger(__name__).info("Category filter '%s' → %d items", category, len(items))

    if limit:
        items = items[:limit]
        logging.getLogger(__name__).info("Limit applied → %d items", len(items))

    logger = logging.getLogger(__name__)
    logger.info("Run ID: RUN_%s | 평가 대상: %d건", run_id, len(items))
    records = []

    for item in tqdm(items, desc="평가 중", unit="건"):
        q = item["question"]
        logger.info("%s | %r", item["query_id"], q[:50])

        record = {
            **item,
            "run_id": f"RUN_{run_id}",
            "top_results": [],
            "hit_at_5": "",
            "recall_at_5": "",
            "refusal": "",
        }

        try:
            results = search_places(q)
            record["top_results"] = results

            if item["eval_type"] == "refusal":
                record["refusal"] = calc_refusal(results)
            else:
                record["hit_at_5"] = calc_hit_at_k(item["answers"], results)
                record["recall_at_5"] = calc_recall_at_k(item["answers"], results)

            if verbose:
                logger.debug(
                    "  answers=%s | top5=%s | hit=%s recall=%s refusal=%s",
                    item["answers"],
                    results,
                    record.get("hit_at_5"),
                    record.get("recall_at_5"),
                    record.get("refusal"),
                )

        except Exception as e:
            logger.warning("  ERROR: %s", e)
            record["error"] = str(e)

        records.append(record)

    out_path = save_results(records, output_path, run_id=run_id)
    _print_summary(records)
    print(f"\n결과 파일: {out_path}")
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="withDOG 장소 검색 품질 평가")
    parser.add_argument("--input", help="평가셋 엑셀 경로 (기본: data/eval/withDOG 평가셋 .xlsx)")
    parser.add_argument("--output", help="결과 저장 경로")
    parser.add_argument("--limit", type=int, help="처음 N건만 실행 (테스트용)")
    parser.add_argument("--category", help="특정 카테고리만 평가")
    parser.add_argument("--verbose", action="store_true", help="상세 로그 출력")
    args = parser.parse_args()

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    _setup_logging(args.verbose, run_id)
    run(
        input_path=args.input,
        output_path=args.output,
        limit=args.limit,
        category=args.category,
        verbose=args.verbose,
        run_id=run_id,
    )


if __name__ == "__main__":
    main()
