# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from sqlalchemy import text
from core.database import get_engine

logger = logging.getLogger(__name__)

# ── 모델별 단가 (USD / 1M 토큰) ──────────────────────────
_PRICES: dict[str, dict[str, float]] = {
    "gpt-4o": {
        "input":  2.50,
        "output": 10.00,
    },
    "gpt-4o-mini": {
        "input":  0.15,
        "output": 0.60,
    },
}

_IMAGE_PRICES: dict[str, float] = {
    "low":    0.011,
    "medium": 0.042,
    "high":   0.167,
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS api_costs (
    id                INT AUTO_INCREMENT PRIMARY KEY,
    called_at         DATETIME NOT NULL,
    model             VARCHAR(50) NOT NULL,
    call_type         VARCHAR(10) NOT NULL,
    prompt_tokens     INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens      INT DEFAULT 0,
    cost_usd          FLOAT NOT NULL,
    note              VARCHAR(100)
) CHARACTER SET utf8mb4;
"""


class OpenAICostTracker:

    def __init__(self):
        # AsyncEngine은 sync 컨텍스트에서 호출할 수 없으므로
        # DDL 실행은 첫 track_* 호출 시점으로 지연한다.
        self._table_ready = False

    async def _ensure_table(self) -> None:
        if self._table_ready:
            return
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(text(SCHEMA))
        self._table_ready = True

    async def _insert(
        self,
        model: str,
        call_type: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost_usd: float,
        note: str,
    ) -> None:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.execute(
                text("""
                    INSERT INTO api_costs
                    (called_at, model, call_type, prompt_tokens, completion_tokens, total_tokens, cost_usd, note)
                    VALUES (:called_at, :model, :call_type, :prompt_tokens, :completion_tokens, :total_tokens, :cost_usd, :note)
                """),
                {
                    "called_at":         datetime.now(),
                    "model":             model,
                    "call_type":         call_type,
                    "prompt_tokens":     prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens":      total_tokens,
                    "cost_usd":          cost_usd,
                    "note":              note,
                }
            )

    async def track_chat(self, response, *, note: str = "") -> None:
        """chat.completions.create() 응답을 받아 비용 기록"""
        await self._ensure_table()

        usage = response.usage
        model = response.model

        price = _PRICES.get(model) or _PRICES.get("gpt-4o")
        cost = (
            usage.prompt_tokens * price["input"] +
            usage.completion_tokens * price["output"]
        ) / 1_000_000

        logger.info(
            "[비용] %s | 입력 %d / 출력 %d 토큰 | $%.6f | %s",
            model, usage.prompt_tokens, usage.completion_tokens, cost, note or "-",
        )
        await self._insert(
            model=model,
            call_type="chat",
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
            cost_usd=cost,
            note=note,
        )

    async def track_image(self, *, quality: str = "low", note: str = "") -> None:
        """이미지 생성 1회 비용 기록"""
        await self._ensure_table()

        cost = _IMAGE_PRICES.get(quality, _IMAGE_PRICES["low"])
        logger.info("[비용] %s | quality=%s | $%.4f | %s", settings.GPT_IMAGE_MODEL, quality, cost, note or "-")
        await self._insert(
            model=settings.GPT_IMAGE_MODEL,
            call_type="image",
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            cost_usd=cost,
            note=note,
        )

    async def get_summary(self) -> dict:
        """누적 비용 요약 반환"""
        await self._ensure_table()

        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(
                text("""
                    SELECT model, call_type, SUM(total_tokens), SUM(cost_usd), COUNT(*)
                    FROM api_costs
                    GROUP BY model, call_type
                """)
            )
            rows = result.fetchall()

            total = (await conn.execute(
                text("SELECT SUM(cost_usd) FROM api_costs")
            )).scalar() or 0.0

        breakdown = [
            {
                "model":        r[0],
                "call_type":    r[1],
                "total_tokens": r[2],
                "cost_usd":     round(r[3], 6),
                "calls":        r[4],
            }
            for r in rows
        ]
        return {"total_cost_usd": round(total, 6), "breakdown": breakdown}
