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

from sqlalchemy import delete, select
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


async def hard_delete_withdrawn_users() -> None:
    """
        탈퇴(deleted_at 기록) 후 10일이 경과한 사용자를 Hard Delete합니다.

        실행 시점: 매일 새벽 3시 (main.py cron 등록)

        처리 순서:
        1. deleted_at IS NOT NULL AND deleted_at <= (현재 - 10일) 조건 조회
        2. 해당 user 들의 모든 image_id 일괄 수집 (users.profile_id + pets.image_id
           + diaries.image_id) + images.file_url 조회 — 단일 read-only 트랜잭션
        3. S3 객체 bulk 삭제 (트랜잭션 외부, image_service._delete_from_s3 호출,
           retry 5회 + exponential backoff. 실패는 logger.error 후 DB 진행)
        4. DB 삭제 단일 트랜잭션:
           - users bulk DELETE → CASCADE 로 pets/diaries/chat_rooms/chat_messages/
             favorite_places 자동 삭제
           - images bulk DELETE — 참조 자식 (users.profile_id / pets.image_id /
             diaries.image_id) 모두 사라졌으니 RESTRICT 통과
        5. 통계 로그 기록
    """
    from core.database import AsyncSessionLocal
    from models.user import User
    from models.pet import Pet
    from models.diary import Diary
    from models.image import Image
    from services.image_service import _delete_from_s3

    if AsyncSessionLocal is None:
        logger.error("[Scheduler] AsyncSessionLocal 미초기화 — Hard Delete 건너뜀")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=10)
    # MySQL 저장값이 UTC naive datetime이므로 naive로 변환
    cutoff_naive = cutoff.replace(tzinfo=None)

    try:
        # ── Step 1·2: target 수집 (read-only 트랜잭션) ────────────────────────
        async with AsyncSessionLocal() as session:
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

            logger.info(
                f"[Scheduler] Processing {len(target_ids)} users for hard delete "
                f"(cutoff={cutoff_naive})"
            )

            # 관련 image_id 일괄 수집 (3 경로 union)
            image_ids: set[int] = set()

            profile_rows = await session.execute(
                select(User.profile_id).where(
                    User.id.in_(target_ids),
                    User.profile_id.is_not(None),
                )
            )
            image_ids.update(profile_rows.scalars().all())

            pet_image_rows = await session.execute(
                select(Pet.image_id).where(
                    Pet.user_id.in_(target_ids),
                    Pet.image_id.is_not(None),
                )
            )
            image_ids.update(pet_image_rows.scalars().all())

            diary_image_rows = await session.execute(
                select(Diary.image_id).where(
                    Diary.user_id.in_(target_ids),
                    Diary.image_id.is_not(None),
                )
            )
            image_ids.update(diary_image_rows.scalars().all())

            # file_url 수집 (S3 삭제용)
            file_urls: list[str] = []
            if image_ids:
                file_url_rows = await session.execute(
                    select(Image.file_url).where(Image.id.in_(image_ids))
                )
                file_urls = list(file_url_rows.scalars().all())

            logger.info(
                f"[Scheduler] Collected {len(image_ids)} image rows / "
                f"{len(file_urls)} S3 objects to cleanup"
            )

        # ── Step 3: S3 bulk 삭제 (트랜잭션 외부) ──────────────────────────────
        s3_deleted: list[str] = []
        s3_failed: list[str] = []
        if file_urls:
            s3_deleted, s3_failed = await _delete_from_s3(file_urls)
            logger.info(
                f"[Scheduler] S3 delete: {len(s3_deleted)} succeeded, "
                f"{len(s3_failed)} failed (DB 진행)"
            )

        # ── Step 4: DB 삭제 단일 트랜잭션 ─────────────────────────────────────
        async with AsyncSessionLocal() as session:
            # users delete → CASCADE 로 pets/diaries/chat_rooms/messages/favorite_places 자동 삭제
            await session.execute(delete(User).where(User.id.in_(target_ids)))

            # images delete — 부모 row 자동 cascade 됐으니 RESTRICT 통과
            if image_ids:
                await session.execute(delete(Image).where(Image.id.in_(image_ids)))

            await session.commit()

        logger.info(
            f"[Scheduler] Hard Delete 완료: users={len(target_ids)} "
            f"(id={target_ids}), images={len(image_ids)}, "
            f"s3_succeeded={len(s3_deleted)}, s3_failed={len(s3_failed)}"
        )

    except Exception as e:
        logger.error(f"[Scheduler] Hard Delete 실패: {e}", exc_info=True)
