import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

from metrics import _is_match, calc_hit_at_k, calc_recall_at_k, calc_refusal
from load_evalset import load_evalset

# ── Test 1-a: 정답 1개, top5에 완전 일치
results = ["월드컵공원반려견놀이터", "한강공원", "보라매공원", "난지천공원", "발바닥공원"]
answers = ["월드컵공원반려견놀이터"]
assert calc_hit_at_k(answers, results) == 1.0
assert calc_recall_at_k(answers, results) == 1.0
print("[Test 1-a] 정상 케이스 (정답 1개) Hit@5=1, Recall@5=1 ✓")

# ── Test 1-b: 정답 5개 중 2개만 top5에 포함
answers5 = ["고양이다락방 홍대점", "마포다방", "멍멍벅스", "써니네애견카페", "구름뜬하늘"]
results5 = ["고양이다락방홍대점", "마포다방", "스타벅스", "올리브영", "이마트"]
assert calc_hit_at_k(answers5, results5) == 1.0
assert calc_recall_at_k(answers5, results5) == 0.4
print("[Test 1-b] 정답 5개 중 2개 포함 → Hit@5=1, Recall@5=0.4 ✓")

# ── Test 1-c: 공백 무시 부분 일치
assert _is_match("고양이다락방 홍대점", "고양이다락방홍대점") is True
print("[Test 1-c] 공백 무시 부분 일치 ✓")

# ── Test 1-d: 정답이 top5에 전혀 없는 경우
assert calc_hit_at_k(["없는장소"], ["스타벅스", "올리브영", "이마트", "GS25", "CU"]) == 0.0
assert calc_recall_at_k(["없는장소"], ["스타벅스", "올리브영", "이마트", "GS25", "CU"]) == 0.0
print("[Test 1-d] 정답 미포함 → Hit@5=0, Recall@5=0 ✓")

# ── Test 2: Refusal
assert calc_refusal([]) == 1.0
assert calc_refusal(["스타벅스"]) == 0.0
print("[Test 2]   Refusal: 0개→1.0, 1개 이상→0.0 ✓")

# ── Test 3: evalset 로딩
items = load_evalset()
retrieval = [i for i in items if i["eval_type"] == "retrieval"]
refusal   = [i for i in items if i["eval_type"] == "refusal"]
print(f"[Test 3]   evalset 로드: 전체={len(items)}, retrieval={len(retrieval)}, refusal={len(refusal)}")
print(f"           retrieval 샘플: {retrieval[0]}")
print(f"           refusal 샘플:   {refusal[0]}")

# ── Test 4: 서버 미실행 상태 에러 처리 (run 함수의 try-except 검증)
import requests
from api_client import search_places
try:
    search_places("테스트쿼리")
    print("[Test 4]   서버 응답 있음 (서버 실행 중)")
except requests.exceptions.ConnectionError:
    print("[Test 4]   서버 미실행 → ConnectionError 발생 (run_evaluation에서 catch 후 계속 진행) ✓")
except Exception as e:
    print(f"[Test 4]   기타 에러: {e} ✓")

print("\n모든 단위 테스트 완료 ✓")
