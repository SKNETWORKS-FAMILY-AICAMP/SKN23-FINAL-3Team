# -*- coding: utf-8 -*-
"""Load personality score vectors from the keywords table."""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

_SCORE_AXES = ("a", "b", "c", "d", "e")


def _normalize_score_vector(raw: Any) -> dict[str, float] | None:
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw:
            return None
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return None

    if not isinstance(raw, dict):
        return None

    scores: dict[str, float] = {}
    for axis in _SCORE_AXES:
        value = raw.get(axis, 0)
        if not isinstance(value, (int, float)):
            return None
        scores[axis] = float(value)
    return scores


async def load_keyword_score_map(
    db: "AsyncSession",
    *,
    category: str,
) -> dict[str, dict[str, float]]:
    """Return {keyword_name: score_vector} loaded from keywords.description."""
    from sqlalchemy import text

    result = await db.execute(
        text(
            """
            SELECT name, description
            FROM keywords
            WHERE category = :category
            """
        ),
        {"category": category.upper()},
    )

    score_map: dict[str, dict[str, float]] = {}
    skipped: list[str] = []
    for row in result.mappings():
        name = row.get("name")
        if not isinstance(name, str) or not name:
            continue

        vector = _normalize_score_vector(row.get("description"))
        if vector is None:
            skipped.append(name)
            continue
        score_map[name] = vector

    if skipped:
        logger.warning(
            "[KeywordScoreLoader] skipped invalid %s keyword score rows: %s",
            category.upper(),
            skipped,
        )
    logger.info(
        "[KeywordScoreLoader] loaded %s keyword score rows for category=%s",
        len(score_map),
        category.upper(),
    )
    return score_map
