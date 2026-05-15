import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - only used in minimal runtimes.
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv()

ROOT_DIR = Path(__file__).parent.parent.parent

DEFAULT_EVAL_PATH = ROOT_DIR / "data" / "eval" / "장소추천 평가셋 NEW.xlsx"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "ai" / "evaluation" / "results"

BASE_URL = os.getenv("EVAL_BASE_URL", "http://localhost:8000")
SEARCH_ENDPOINT = f"{BASE_URL}/api/places/search"

REQUEST_TIMEOUT = int(os.getenv("EVAL_TIMEOUT", "30"))

EVAL_SHEET_INDEX = 0

REFUSAL_CATEGORY = "오류/범위 밖"

# GPS 평가셋 기준 위치: 서울특별시 금천구 가산동 670 인근.
# 자동 평가가 실행 환경의 실제 현재 위치에 흔들리지 않도록 고정 좌표를 사용한다.
EVAL_USER_LAT = float(os.getenv("EVAL_USER_LAT", "37.46674548"))
EVAL_USER_LNG = float(os.getenv("EVAL_USER_LNG", "126.886719"))
