"""
OpenAI API 비용 추적 유틸
호출마다 토큰 수와 예상 비용(USD)을 로그에 남기고 SQLite에 누적 저장합니다.
"""

import logging
from datetime import datetime
from pathlib import Path

import aiosqlite

logger = logging.getLogger(__name__)

DB_PATH = Path(__file__).parent.parent.parent / "db" / "diary.db"

# ── 모델별 단가 (USD / 1M 토큰) ──────────────────────────
# https://openai.com/pricing 기준 (2025-04 시점)
_PRICES: dict[str, dict[str, float]] = {
    "gpt-4o": {
        "input":  2.50,   # $2.50 / 1M input tokens
        "output": 10.00,  # $10.00 / 1M output tokens
    },
    "gpt-4o-mini": {
        "input":  0.15,
        "output": 0.60,
    },
}

# gpt-image-1: 품질별 고정 단가 (이미지 1장)
_IMAGE_PRICES: dict[str, float] = {
    "low":    0.011,
    "medium": 0.042,
    "high":   0.167,
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS api_costs (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    called_at    TEXT NOT NULL,
    model        TEXT NOT NULL,
    call_type    TEXT NOT NULL,   -- 'chat' | 'image'
    prompt_tokens     INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens      INTEGER DEFAULT 0,
    cost_usd     REAL NOT NULL,
    note         TEXT            -- 어떤 기능에서 호출했는지 (diary / weekly / monthly)
);
"""


async def _ensure_table() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(SCHEMA)
        await db.commit()


async def _insert(
    model: str,
    call_type: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    cost_usd: float,
    note: str,
) -> None:
    await _ensure_table()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO api_costs
               (called_at, model, call_type, prompt_tokens, completion_tokens, total_tokens, cost_usd, note)
               VALUES (?,?,?,?,?,?,?,?)""",
            (datetime.now().isoformat(), model, call_type,
             prompt_tokens, completion_tokens, total_tokens, cost_usd, note),
        )
        await db.commit()


# ── 공개 함수 ──────────────────────────────────────────
async def track_chat(response, *, note: str = "") -> None:
    """chat.completions.create() 응답을 받아 비용 기록"""
    usage = response.usage
    model = response.model  # 실제 사용된 모델명

    price = _PRICES.get(model) or _PRICES.get("gpt-4o")  # 모르는 모델은 gpt-4o 단가 적용
    cost = (usage.prompt_tokens * price["input"] + usage.completion_tokens * price["output"]) / 1_000_000

    logger.info(
        "[비용] %s | 입력 %d / 출력 %d 토큰 | $%.6f | %s",
        model, usage.prompt_tokens, usage.completion_tokens, cost, note or "-",
    )
    await _insert(
        model=model,
        call_type="chat",
        prompt_tokens=usage.prompt_tokens,
        completion_tokens=usage.completion_tokens,
        total_tokens=usage.total_tokens,
        cost_usd=cost,
        note=note,
    )


async def track_image(*, quality: str = "low", note: str = "") -> None:
    """이미지 생성 1회 비용 기록"""
    cost = _IMAGE_PRICES.get(quality, _IMAGE_PRICES["low"])
    logger.info("[비용] gpt-image-1 | quality=%s | $%.4f | %s", quality, cost, note or "-")
    await _insert(
        model="gpt-image-1",
        call_type="image",
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
        cost_usd=cost,
        note=note,
    )


async def get_summary() -> dict:
    """누적 비용 요약 반환"""
    await _ensure_table()
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT model, call_type, SUM(total_tokens), SUM(cost_usd), COUNT(*) FROM api_costs GROUP BY model, call_type"
        ) as cur:
            rows = await cur.fetchall()
        async with db.execute("SELECT SUM(cost_usd) FROM api_costs") as cur:
            total = (await cur.fetchone())[0] or 0.0

    breakdown = [
        {"model": r[0], "call_type": r[1], "total_tokens": r[2], "cost_usd": round(r[3], 6), "calls": r[4]}
        for r in rows
    ]
    return {"total_cost_usd": round(total, 6), "breakdown": breakdown}
