# -*- coding: utf-8 -*-
"""
services/scheduler.py
---------------------
APScheduler 배치 작업 정의.

등록된 배치:
    - hard_delete_withdrawn_users(): 탈퇴 후 10일 경과한 사용자 Hard Delete
        → main.py lifespan에서 매일 새벽 3시 실행 등록

실행 방식:
    - AsyncIOScheduler 사용 (FastAPI 비동기 이벤트 루프와 통합)
    - DB 세션은 AsyncSessionLocal 팩토리를 직접 사용 (Depends 없이)
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

logger = logging.getLogger(__name__)


async def hard_delete_withdrawn_users() -> None:
    """
        탈퇴(deleted_at 기록) 후 10일이 경과한 사용자를 Hard Delete합니다.

        실행 시점: 매일 새벽 3시 (main.py cron 등록)

        처리 순서:
        1. deleted_at IS NOT NULL AND deleted_at <= (현재 - 10일) 조건 조회
        2. 해당 사용자 행 물리 삭제 (CASCADE로 pets, chat_rooms, diaries 연쇄 삭제)
        3. 삭제 건수 로그 기록
    """
    from core.database import AsyncSessionLocal
    from models.user import User

    if AsyncSessionLocal is None:
        logger.error("[Scheduler] AsyncSessionLocal 미초기화 — Hard Delete 건너뜀")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=10)
    # MySQL 저장값이 UTC naive datetime이므로 naive로 변환
    cutoff_naive = cutoff.replace(tzinfo=None)

    try:
        async with AsyncSessionLocal() as session:
            # 삭제 대상 미리 조회 (로그용)
            result = await session.execute(
                select(User.id).where(
                    User.deleted_at.is_not(None),
                    User.deleted_at <= cutoff_naive,
                )
            )
            target_ids = [row[0] for row in result.fetchall()]

            if not target_ids:
                logger.info("[Scheduler] Hard Delete 대상 없음")
                return

            # Hard Delete 실행
            await session.execute(
                delete(User).where(User.id.in_(target_ids))
            )
            await session.commit()

            logger.info(
                f"[Scheduler] Hard Delete 완료: {len(target_ids)}명 삭제 "
                f"(id={target_ids})"
            )

    except Exception as e:
        logger.error(f"[Scheduler] Hard Delete 실패: {e}", exc_info=True)
