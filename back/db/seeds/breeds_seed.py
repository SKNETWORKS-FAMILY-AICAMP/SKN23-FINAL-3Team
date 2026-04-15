# -*- coding: utf-8 -*-
"""
back/db/seeds/breeds_seed.py
-----------------------------
breeds 테이블에 견종 마스터 데이터를 적재하는 시드 스크립트.

embed_breeds.py 와 동일한 방식으로:
  1. The Dog API 에서 전체 견종 목록을 가져옵니다.
  2. GPT-4.1-mini 로 견종명을 한국어로 번역합니다.
  3. breeds 테이블에 upsert (이미 존재하면 name_ko / name_en 업데이트) 합니다.

[TOP10 설정]
  국내 인기 견종 10개는 `TOP10_NAMES` 에 영문 견종명(소문자)으로 지정합니다.

실행 방법::

    # 프로젝트 루트에서
    python back/db/seeds/breeds_seed.py

    # back/ 디렉토리에서
    python db/seeds/breeds_seed.py

    # local SSH 터널 환경이라면 SERVER=local 이 .env 에 설정되어 있어야 합니다.
"""

from __future__ import annotations

import asyncio
import os
import sys

import httpx
from dotenv import load_dotenv
from openai import OpenAI

# ── 경로 설정: back/api 를 sys.path 에 추가 ────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))            # back/db/seeds/
_BACK_API = os.path.normpath(os.path.join(_HERE, "../../api"))  # back/api/
sys.path.insert(0, _BACK_API)

load_dotenv(os.path.normpath(os.path.join(_HERE, "../../../.env")))

# ── 설정 ──────────────────────────────────────────────────────────────────
DOG_API_URL = "https://api.thedogapi.com/v1/breeds"
DOG_API_KEY = os.getenv("DOG_API_KEY", "")

# 국내 인기 견종 TOP10 (The Dog API 영문명 소문자 기준)
TOP10_NAMES: set[str] = {
    "maltese",
    "poodle",
    "golden retriever",
    "french bulldog",
    "shih tzu",
    "bichon frise",
    "labrador retriever",
    "chihuahua",
    "yorkshire terrier",
    "pomeranian",
}

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ── The Dog API 호출 ───────────────────────────────────────────────────────
def fetch_breeds() -> list[dict]:
    """The Dog API 에서 전체 견종 목록을 가져옵니다."""
    print("The Dog API 호출 중...")
    headers = {}
    if DOG_API_KEY:
        headers["x-api-key"] = DOG_API_KEY

    response = httpx.get(DOG_API_URL, headers=headers, timeout=30)
    response.raise_for_status()
    breeds = response.json()
    print(f"총 {len(breeds)}개 견종 수집 완료!")
    return breeds


# ── GPT 번역 ───────────────────────────────────────────────────────────────
def translate_breed_name(breed_name: str) -> str:
    """영문 견종명 → 한국어 번역 (GPT-4.1-mini)."""
    response = openai_client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "강아지 견종명을 한국어로 번역해주세요. "
                    "한국어 견종명만 답하세요. "
                    "번역이 없으면 영문 그대로 답하세요."
                ),
            },
            {"role": "user", "content": breed_name},
        ],
        max_tokens=50,
    )
    return response.choices[0].message.content.strip()


# ── DB 적재 (비동기) ───────────────────────────────────────────────────────
async def seed(ssh_tunnel: bool = False) -> None:
    """
    breeds 테이블에 시드 데이터를 적재합니다.

    Args:
        ssh_tunnel: True 이면 local SSH 터널을 먼저 엽니다.
    """
    import core.database
    from core.config import settings
    from models.breed import Breed
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

    try:
        # ── 견종 데이터 수집 ──────────────────────────────────────────────
        breeds_raw = fetch_breeds()

        # ── DB 적재 ───────────────────────────────────────────────────────
        inserted = 0
        updated = 0

        async with core.database.AsyncSessionLocal() as session:
            for i, breed in enumerate(breeds_raw):
                breed_name_en: str = breed.get("name", "")
                if not breed_name_en:
                    continue

                print(f"  [{i + 1}/{len(breeds_raw)}] {breed_name_en} 번역 중...")
                breed_name_ko = translate_breed_name(breed_name_en)
                is_top10 = breed_name_en.lower() in TOP10_NAMES

                # 영문명 기준으로 기존 레코드 조회 (upsert)
                result = await session.execute(
                    select(Breed).where(Breed.name_en == breed_name_en)
                )
                existing: Breed | None = result.scalar_one_or_none()

                if existing:
                    existing.name_ko = breed_name_ko
                    existing.name_en = breed_name_en
                    existing.top10 = is_top10
                    updated += 1
                    print(f"    → 업데이트: {breed_name_ko} (top10={is_top10})")
                else:
                    new_breed = Breed(
                        name_ko=breed_name_ko,
                        name_en=breed_name_en,
                        top10=is_top10,
                    )
                    session.add(new_breed)
                    inserted += 1
                    print(f"    → 삽입: {breed_name_ko} (top10={is_top10})")

            await session.commit()

        print(f"\n✅ breeds 테이블 시드 완료!")
        print(f"   삽입: {inserted}개 / 업데이트: {updated}개")
        print(f"   TOP10 해당 견종: {[b['name'] for b in breeds_raw if b.get('name', '').lower() in TOP10_NAMES]}")

    finally:
        if tunnel and tunnel.is_active:
            tunnel.stop()
            print("SSH 터널 종료")


# ── 진입점 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(seed())
