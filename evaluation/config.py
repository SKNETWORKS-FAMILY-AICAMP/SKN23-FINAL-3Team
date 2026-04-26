import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent

DEFAULT_EVAL_PATH = ROOT_DIR / "data" / "eval" / "withDOG 평가셋 .xlsx"
DEFAULT_OUTPUT_DIR = ROOT_DIR / "evaluation" / "results"

BASE_URL = os.getenv("EVAL_BASE_URL", "http://localhost:8000")
SEARCH_ENDPOINT = f"{BASE_URL}/api/places/search"

REQUEST_TIMEOUT = int(os.getenv("EVAL_TIMEOUT", "30"))

EVAL_SHEET_INDEX = 0

REFUSAL_CATEGORY = "오류/범위 밖"
