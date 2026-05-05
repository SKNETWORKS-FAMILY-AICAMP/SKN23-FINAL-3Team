"""Ablation 평가: RAG only / RDB only / Combined × Top-N(1,3,5,10,20).

실행 예시:
    python run_ablation.py
    python run_ablation.py --input path/to/evalset.xlsx --output path/to/result.xlsx
    python run_ablation.py --limit 10   # 테스트용 10건만
"""
import argparse
import logging
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))

from api_client import parse_query_eval, search_places_eval as search_places
from load_evalset import load_evalset
from metrics import calc_hit_at_k, calc_recall_at_k
from save_results import save_ablation_results

MODES = ["combined", "rdb_only", "rag_only"]
K_VALUES = [1, 3, 5, 10, 20]
MAX_K = max(K_VALUES)

LOG_DIR = Path(__file__).parent / "logs"


def _setup_logging(run_id: str) -> None:
    LOG_DIR.mkdir(exist_ok=True)
    log_file = LOG_DIR / f"ablation_{run_id}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def _print_summary(records: list[dict]) -> None:
    retrieval = [
        r for r in records
        if r.get("eval_type") == "retrieval" and not r.get("error") and r.get("hit_at_k") != ""
    ]

    by_mode_k: dict = defaultdict(list)
    for r in retrieval:
        by_mode_k[(r["mode"], r["k"])].append(r)

    print("\n" + "=" * 60)
    print("Ablation 평가 결과 요약")
    print("=" * 60)
    print(f"\n{'mode':<12} {'k':>4} {'n':>5}  {'Hit@k':>7}  {'Recall@k':>9}")
    print("-" * 45)
    for (mode, k), items in sorted(by_mode_k.items(), key=lambda x: (x[0][0], x[0][1])):
        hit = sum(i["hit_at_k"] for i in items) / len(items)
        recall = sum(i["recall_at_k"] for i in items) / len(items)
        print(f"{mode:<12} {k:>4} {len(items):>5}  {hit:>7.3f}  {recall:>9.3f}")
    print("=" * 60)


def run(
    input_path: str = None,
    output_path: str = None,
    limit: int = None,
) -> None:
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    _setup_logging(run_id)
    logger = logging.getLogger(__name__)

    items = load_evalset(input_path)
    retrieval_items = [i for i in items if i["eval_type"] == "retrieval"]

    if limit:
        retrieval_items = retrieval_items[:limit]
        logger.info("Limit applied → %d items", len(retrieval_items))

    logger.info(
        "Ablation 시작: %d건 × %d모드 (k=%s)",
        len(retrieval_items), len(MODES), K_VALUES,
    )

    # 모든 질문을 LLM으로 한 번만 파싱해서 캐싱 (모드 루프에서 재사용)
    logger.info("쿼리 사전 파싱 시작: %d건", len(retrieval_items))
    parsed_cache: dict[str, dict | None] = {}
    for item in tqdm(retrieval_items, desc="pre-parse ", unit="건"):
        parsed_cache[item["query_id"]] = parse_query_eval(item["question"])
    logger.info("쿼리 사전 파싱 완료")

    all_records = []

    for mode in MODES:
        logger.info("모드 시작: %s", mode)
        for item in tqdm(retrieval_items, desc=f"{mode:<12}", unit="건"):
            top_results = []
            error = None

            try:
                # MAX_K개를 한 번만 조회하고 k별 메트릭은 슬라이싱으로 계산
                # 사전 파싱된 결과를 전달해 서버에서 LLM 파싱 호출을 생략
                top_results = search_places(
                    item["question"],
                    n_results=MAX_K,
                    mode=mode,
                    parsed=parsed_cache.get(item["query_id"]),
                )
            except Exception as e:
                logger.warning("  ERROR (%s) %s: %s", mode, item["query_id"], e)
                error = str(e)

            for k in K_VALUES:
                all_records.append({
                    "run_id": f"RUN_{run_id}",
                    "mode": mode,
                    "k": k,
                    **item,
                    "top_results": top_results,
                    "hit_at_k": calc_hit_at_k(item["answers"], top_results, k=k) if not error else "",
                    "recall_at_k": calc_recall_at_k(item["answers"], top_results, k=k) if not error else "",
                    "error": error,
                })

    out_path = save_ablation_results(all_records, output_path, run_id=run_id)
    _print_summary(all_records)
    print(f"\n결과 파일: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ablation 평가 (RAG/RDB/Combined × Top-N)")
    parser.add_argument("--input", help="평가셋 엑셀 경로")
    parser.add_argument("--output", help="결과 저장 경로")
    parser.add_argument("--limit", type=int, help="처음 N건만 실행 (테스트용)")
    args = parser.parse_args()
    run(input_path=args.input, output_path=args.output, limit=args.limit)


if __name__ == "__main__":
    main()
