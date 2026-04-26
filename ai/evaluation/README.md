# withDOG 장소 검색 평가 스크립트

장소 검색 API(`/api/places/search`)의 품질을 정량 측정하는 자동화 평가 도구.

---

## 설치

```bash
# 프로젝트 루트에서 venv 활성화 후
pip install tqdm openpyxl pandas
```

환경변수 (`.env` 또는 직접 설정):

```env
EVAL_BASE_URL=http://localhost:8000   # 기본값, 서버 주소가 다를 때만 변경
EVAL_TIMEOUT=30                       # API 호출 타임아웃 (초)
```

---

## 실행

### 기본 (전체 150건)

```bash
python evaluation/run_evaluation.py
```

### 옵션

```bash
# 처음 10건만 (빠른 확인용)
python evaluation/run_evaluation.py --limit 10

# 특정 카테고리만
python evaluation/run_evaluation.py --category "오류/범위 밖"
python evaluation/run_evaluation.py --category "위치 기반 근처"

# 상세 로그 (각 쿼리별 top5 결과 출력)
python evaluation/run_evaluation.py --limit 10 --verbose

# 결과 파일 경로 지정
python evaluation/run_evaluation.py --output evaluation/results/baseline.xlsx

# 입력 파일 직접 지정
python evaluation/run_evaluation.py --input "data/eval/withDOG 평가셋 .xlsx"
```

---

## 출력 해석

### 콘솔 요약

```
============================================================
평가 결과 요약
============================================================

[전체 Retrieval] n=118
  Hit@5    : 0.5254 (52.5%)   ← Top-5 안에 정답이 하나라도 있는 비율
  Recall@5 : 0.4102 (41.0%)   ← 정답 여러 개일 때 Top-5에 포함된 비율

[전체 Refusal] n=32
  Refusal Rate : 0.5938 (59.4%)  ← 서울 외 지역 등 범위 밖 질문을 올바르게 거절한 비율

[카테고리별]
카테고리                    n    Hit@5   Recall@5   Refusal
----------------------------------------------------------
복합 조건                  29    0.483      0.352         -
위치 기반 근처             16    0.250      0.198         -
오류/범위 밖               32        -          -     0.594
...
============================================================
```

### 결과 엑셀 (`evaluation/results/eval_results_YYYYMMDD_HHMMSS.xlsx`)

| 컬럼 | 설명 |
|---|---|
| `run_id` | 실행 식별자 (`RUN_20260426_183000`) — 여러 번 실행 결과 구분용 |
| `query_id` | 질문 ID (`Q_A_003`) |
| `카테고리` | 질문 유형 |
| `사용자질문` | 실제 쿼리 |
| `정답` | 정답 장소 이름(들) |
| `top1`~`top5` | API가 반환한 장소 이름 순서대로 |
| `hit_at_5` | 1 (정답 포함) / 0 (미포함) / 빈칸 (refusal 케이스) |
| `recall_at_5` | 0.0 ~ 1.0 / 빈칸 (refusal 케이스) |
| `refusal` | 1 (올바른 거절) / 0 (잘못 반환) / 빈칸 (retrieval 케이스) |
| `비고` | 에러 메시지 또는 원본 비고 |

### 로그 파일 (`evaluation/logs/run_YYYYMMDD_HHMMSS.log`)

실행마다 로그 파일이 생성되어 각 쿼리의 실행 기록이 남음.

---

## 성능 개선 추적 방법

개선 전/후에 각각 실행하고 결과 파일을 비교한다.

```bash
# 1. 개선 전 baseline 측정
python evaluation/run_evaluation.py --output evaluation/results/before.xlsx

# 2. 검색 로직 개선 작업 수행

# 3. 개선 후 측정
python evaluation/run_evaluation.py --output evaluation/results/after.xlsx
```

결과 파일의 `run_id` 컬럼으로 두 실행을 구분할 수 있음.

**보고 예시:**
> 초기 평가(RUN_20260426)에서 전체 Hit@5 52.5%, '위치 기반 근처' 카테고리가 25.0%로 
> 가장 낮았음. query_parser 개선 후 재평가(RUN_20260501)에서 '위치 기반 근처' 62.5%, 
> 전체 Hit@5 71.2%로 향상.

---

## 트러블슈팅

### API 연결 실패 (`ConnectionError`)

```
ERROR: HTTPConnectionPool(host='localhost', port=8000): Max retries exceeded
```

→ 백엔드 서버가 실행 중인지 확인: `cd back && uvicorn api.main:app --reload`

→ 서버 주소가 다르면 `.env`에서 `EVAL_BASE_URL` 변경

### 엑셀 파일을 찾을 수 없음

```
FileNotFoundError: data/eval/withDOG 평가셋 .xlsx
```

→ 프로젝트 루트에서 실행하고 있는지 확인

→ 파일 경로 직접 지정: `--input "경로/파일명.xlsx"`

### 인코딩 에러 (Windows)

```bash
# UTF-8 모드로 실행
python -X utf8 evaluation/run_evaluation.py
```

### 결과 파일 저장 실패 (권한 오류)

→ 결과 파일이 Excel에서 열려 있는 경우 발생. Excel을 닫고 재실행.

---

## 평가셋 구조

- **파일**: `data/eval/withDOG 평가셋 .xlsx` (첫 번째 시트)
- **총 150건**: retrieval 118건 + refusal(오류/범위 밖) 32건
- **정답 비교 방식**: 장소 이름 기준 부분 일치 (공백·특수문자 무시)

| 카테고리 | 건수 | 평가 방식 |
|---|---|---|
| 복합 조건 | 29 | Hit@5, Recall@5 |
| 지역 x 장소유형 | 27 | Hit@5, Recall@5 |
| 주관 형용사 | 21 | Hit@5, Recall@5 |
| 위치 기반 근처 | 16 | Hit@5, Recall@5 |
| 동반 조건 특수 | 11 | Hit@5, Recall@5 |
| 실내/실외 | 11 | Hit@5, Recall@5 |
| 시간 조건 | 11 | Hit@5, Recall@5 |
| 편의시설 (주차) | 9 | Hit@5, Recall@5 |
| **오류/범위 밖** | **32** | **Refusal Rate** |
