# -*- coding: utf-8 -*-
"""
Calculate profile type_id values from selected_tags.

This script:
  1. Loads keyword score vectors from the keywords table.
  2. Uses DogScorer.classify_type / OwnerScorer.classify_type.
  3. Upserts type keywords as PET_TYPE / USER_TYPE rows.
  4. Updates pets.type_id and users.type_id with the calculated type keyword id.
     Rows without selected_tags are set to NULL.

Run from the project root:
    python back/data/scripts/migrate_profile_types.py
"""

from __future__ import annotations

import asyncio
import os
import sys

from dotenv import load_dotenv
from sshtunnel import SSHTunnelForwarder
from sqlalchemy import select, text

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.normpath(os.path.join(_HERE, "../../.."))
_BACK_API = os.path.normpath(os.path.join(_HERE, "../../api"))

sys.path.insert(0, _PROJECT_ROOT)
sys.path.insert(0, _BACK_API)

load_dotenv(os.path.join(_PROJECT_ROOT, ".env"))

import core.database  # noqa: E402
from ai.scorers.dog_scorer import DogScorer  # noqa: E402
from ai.scorers.owner_scorer import OwnerScorer  # noqa: E402
from core.config import settings  # noqa: E402
from models.keyword import Keyword  # noqa: E402
from models.pet import Pet  # noqa: E402
from models.user import User  # noqa: E402

def _pick_type_keyword(candidates: list[Keyword], *, type_key: str) -> Keyword | None:
    """Pick the canonical type row when duplicate type keywords already exist."""
    if not candidates:
        return None

    for keyword in candidates:
        if keyword.description == type_key and keyword.name != type_key:
            return keyword
    for keyword in candidates:
        if keyword.description == type_key:
            return keyword
    return candidates[0]


async def _ensure_type_keywords(
    session,
    *,
    category: str,
    scorer,
) -> dict[str, int]:
    type_category = f"{category}_TYPE"
    type_ids: dict[str, int] = {}

    for type_key in scorer._AXIS_TO_TYPE.values():
        type_name = scorer.get_type_name(type_key)
        result = await session.execute(
            select(Keyword).where(
                Keyword.category == type_category,
                (
                    (Keyword.description == type_key)
                    | (Keyword.name == type_key)
                ),
            )
        )
        keyword = _pick_type_keyword(result.scalars().all(), type_key=type_key)
        if keyword is None:
            keyword = Keyword(
                category=type_category,
                name=type_name,
                description=type_key,
            )
            session.add(keyword)
            await session.flush()
        elif keyword.description != type_key or keyword.name == type_key:
            keyword.name = type_name
            keyword.description = type_key
        type_ids[type_key] = keyword.id

    return type_ids


def _coerce_tags(raw_tags) -> list[str]:
    if not isinstance(raw_tags, list):
        return []
    return [tag for tag in raw_tags if isinstance(tag, str) and tag.strip()]


async def _assert_pet_type_id_nullable(session) -> None:
    result = await session.execute(
        text(
            """
            SELECT IS_NULLABLE
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'pets'
              AND COLUMN_NAME = 'type_id'
            """
        )
    )
    is_nullable = result.scalar_one_or_none()
    if is_nullable != "YES":
        raise RuntimeError(
            "pets.type_id must be nullable before this migration. "
            "Run: ALTER TABLE pets MODIFY COLUMN type_id BIGINT NULL COMMENT '대표 성격 키워드 ID';"
        )


async def migrate() -> None:
    tunnel = None
    db_host = settings.DB_HOST
    db_port = settings.DB_PORT

    if settings.SERVER == "local":
        print("SSH tunnel connecting...")
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
        print(f"SSH tunnel connected: localhost:{db_port}")

    core.database.init_engine(host=db_host, port=db_port)

    try:
        async with core.database.AsyncSessionLocal() as session:
            await _assert_pet_type_id_nullable(session)

            dog_scorer = DogScorer()
            owner_scorer = OwnerScorer()
            await dog_scorer.load_from_db(session)
            await owner_scorer.load_from_db(session)

            pet_type_ids = await _ensure_type_keywords(
                session,
                category="PET",
                scorer=dog_scorer,
            )
            user_type_ids = await _ensure_type_keywords(
                session,
                category="USER",
                scorer=owner_scorer,
            )

            updated_pets = 0
            skipped_pets = 0
            pet_result = await session.execute(select(Pet))
            for pet in pet_result.scalars().all():
                tags = _coerce_tags(pet.selected_tags)
                if not tags:
                    if pet.type_id is not None:
                        pet.type_id = None
                        updated_pets += 1
                    skipped_pets += 1
                    continue
                type_key = dog_scorer.classify_type(tags)
                new_type_id = pet_type_ids[type_key]
                if pet.type_id != new_type_id:
                    pet.type_id = new_type_id
                    updated_pets += 1

            updated_users = 0
            skipped_users = 0
            user_result = await session.execute(select(User))
            for user in user_result.scalars().all():
                tags = _coerce_tags(user.selected_tags)
                if not tags:
                    if user.type_id is not None:
                        user.type_id = None
                        updated_users += 1
                    skipped_users += 1
                    continue
                type_key = owner_scorer.classify_type(tags)
                new_type_id = user_type_ids[type_key]
                if user.type_id != new_type_id:
                    user.type_id = new_type_id
                    updated_users += 1

            await session.commit()

            print("Profile type migration completed.")
            print(f"  pets updated: {updated_pets}, skipped(no tags): {skipped_pets}")
            print(f"  users updated: {updated_users}, skipped(no tags): {skipped_users}")
    finally:
        await core.database.close_db()
        if tunnel and tunnel.is_active:
            tunnel.stop()
            print("SSH tunnel closed.")


if __name__ == "__main__":
    asyncio.run(migrate())
