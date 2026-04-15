# -*- coding: utf-8 -*-
"""
back/db/seeds/keywords_seed.py
-------------------------------
keywords 테이블에 성향 태그 마스터 데이터를 적재하는 시드 스크립트.

ai/utils/scoring.py 의 DOG_TAG_SCORES, OWNER_TAG_SCORES 를 읽어:
  - category : DOG_TAG_SCORES → "PET" / OWNER_TAG_SCORES → "USER"
  - name      : 딕셔너리 키 (태그명)
  - description: 딕셔너리 값 (점수 딕셔너리를 문자열로 저장)

이미 존재하는 항목은 description 만 업데이트합니다 (upsert).

실행 방법::

    # 프로젝트 루트에서
    python back/db/seeds/keywords_seed.py

    # back/ 디렉토리에서
    python db/seeds/keywords_seed.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

from dotenv import load_dotenv

# ── 경로 설정 ─────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))                # back/db/seeds/
_BACK_API = os.path.normpath(os.path.join(_HERE, "../../api"))    # back/api/
_AI_UTILS = os.path.normpath(os.path.join(_HERE, "../../../ai"))  # ai/

sys.path.insert(0, _BACK_API)
sys.path.insert(0, _AI_UTILS)

load_dotenv(os.path.normpath(os.path.join(_HERE, "../../../.env")))

# ── scoring.py 에서 태그 점수표 임포트 ────────────────────────────────────
from utils.scoring import DOG_TAG_SCORES, OWNER_TAG_SCORES  # noqa: E402


# ── DB 적재 (비동기) ───────────────────────────────────────────────────────
async def seed() -> None:
    """keywords 테이블에 시드 데이터를 적재합니다."""
    import core.database
    from core.config import settings
    from models.keyword import Keyword
    from sqlalchemy import select

    # ── SSH 터널 (local 환경) ─────────────────────────────────────────────
    db_host = settings.DB_HOST
    db_port = settings.DB_PORT

    tunnel = None
    if settings.SERVER == "local":
        print("SSH 터널 연결 중...")
        from sshtunnel import SSHTunnelForwarder
        tunnel = SSHTunnelForwarder(
            (settings.SSH_HOST, settings.SSH_PORT),
            ssh_username=settings.SSH_USER,
            ssh_pkey=settings.SSH_PKEY,
            remote_bind_address=(settings.DB_HOST, settings.DB_PORT),
            local_bind_address=("127.0.0.1",),
        )
        tunnel.start()
        db_host = "127.0.0.1"
        db_port = tunnel.local_bind_port
        print(f"SSH 터널 완료: localhost:{db_port}")

    # ── DB 엔진 초기화 ────────────────────────────────────────────────────
    core.database.init_engine(host=db_host, port=db_port)

    # ── 적재할 데이터 구성 ─────────────────────────────────────────────────
    # (category, name, description) 튜플 목록
    rows: list[tuple[str, str, str]] = []

    for name, scores in DOG_TAG_SCORES.items():
        rows.append(("PET", name, json.dumps(scores, ensure_ascii=False)))

    for name, scores in OWNER_TAG_SCORES.items():
        rows.append(("USER", name, json.dumps(scores, ensure_ascii=False)))

    try:
        inserted = 0
        updated = 0

        async with core.database.AsyncSessionLocal() as session:
            for category, name, description in rows:
                result = await session.execute(
                    select(Keyword).where(
                        Keyword.category == category,
                        Keyword.name == name,
                    )
                )
                existing: Keyword | None = result.scalar_one_or_none()

                if existing:
                    existing.description = description
                    updated += 1
                    print(f"  [UPDATE] ({category}) {name}")
                else:
                    session.add(Keyword(
                        category=category,
                        name=name,
                        description=description,
                    ))
                    inserted += 1
                    print(f"  [INSERT] ({category}) {name}")

            await session.commit()

        print(f"\n✅ keywords 테이블 시드 완료!")
        print(f"   삽입: {inserted}개 / 업데이트: {updated}개")
        print(f"   PET 태그: {len(DOG_TAG_SCORES)}개 / USER 태그: {len(OWNER_TAG_SCORES)}개")

    finally:
        if tunnel and tunnel.is_active:
            tunnel.stop()
            print("SSH 터널 종료")


# ── 진입점 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(seed())
