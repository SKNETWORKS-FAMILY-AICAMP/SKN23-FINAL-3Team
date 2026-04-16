# -*- coding: utf-8 -*-
"""
back/db/seeds/breeds_seed.py
-----------------------------
breeds 테이블에 견종 마스터 데이터를 적재하는 시드 스크립트.

[TOP10 설정]
  국내 인기 견종 10개는 `TOP10_NAMES` 에 영문 견종명(소문자)으로 지정합니다.

실행 방법::

    # 프로젝트 루트에서
    python back/db/seeds/breeds_seed.py
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

    try:
        response = httpx.get(DOG_API_URL, headers=headers, timeout=30)
        response.raise_for_status()
        breeds = response.json()
        print(f"총 {len(breeds)}개 견종 수집 완료!")
        return breeds
    except Exception as e:
        print(f"[ERROR] The Dog API 호출 실패: {e}")
        return []


# ── GPT 번역 ───────────────────────────────────────────────────────────────
def translate_breed_name(breed_name: str) -> str:
    """영문 견종명 → 한국어 번역 (GPT-4.1-mini)."""
    try:
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
    except Exception as e:
        print(f"[ERROR] 반려견 이름 번역 실패 ({breed_name}): {e}")
        return breed_name


def classify_size(metric_weight_str: str | None) -> str | None:
    """체중 정보를 바탕으로 소/중/대형견 분류를 수행합니다."""
    if not metric_weight_str or metric_weight_str.strip() == "NaN":
        return None
    try:
        parts = metric_weight_str.split("-")
        max_weight = float(parts[-1].strip())
        if max_weight < 10:
            return "small"
        elif max_weight < 25:
            return "medium"
        else:
            return "large"
    except Exception as e:
        # 파싱 실패 시 NULL 처리
        return None


def get_activity_level(temperament: str | None) -> str:
    if not temperament:
        return "medium"
    t = temperament.lower()
    high = ["energetic", "active", "playful", "spirited", "lively", "high-energy", "athletic"]
    low = ["calm", "gentle", "quiet", "lazy", "docile", "easygoing", "laid-back"]
    if any(k in t for k in high):
        return "high"
    elif any(k in t for k in low):
        return "low"
    else:
        return "medium"


# ── DB 적재 (비동기) ───────────────────────────────────────────────────────
async def seed(ssh_tunnel: bool = False) -> None:
    import core.database
    from core.config import settings
    from models.breed import Breed
    from sqlalchemy import text

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
        if not breeds_raw:
            print("데이터를 가져오지 못했습니다. DB 갱신을 취소합니다.")
            return

        # ── DB 적재 ───────────────────────────────────────────────────────
        inserted = 0

        async with core.database.AsyncSessionLocal() as session:
            print("기존 breeds 데이터 삭제 및 AUTO_INCREMENT 초기화 진행 중...")
            
            # 외래키 제약조건이 있을 수 있으므로 FK 체크 해제 후 진행하는 것이 안전 (필요 시)
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            await session.execute(text("DELETE FROM breeds;"))
            await session.execute(text("ALTER TABLE breeds AUTO_INCREMENT = 1;"))
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            await session.commit()
            
            for i, breed in enumerate(breeds_raw):
                breed_name_en: str = breed.get("name", "")
                if not breed_name_en:
                    continue

                print(f"  [{i + 1}/{len(breeds_raw)}] {breed_name_en} 번역 및 파싱 중...")
                breed_name_ko = translate_breed_name(breed_name_en)
                is_top10 = breed_name_en.lower() in TOP10_NAMES
                
                weight_meta = breed.get("weight", {})
                metric_weight = weight_meta.get("metric")
                size = classify_size(metric_weight)

                temperament = breed.get("temperament", None)
                activity_level = get_activity_level(temperament)
                breed_group = breed.get("breed_group", None)
                
                image_meta = breed.get("image", {})
                image_url = image_meta.get("url", None)

                new_breed = Breed(
                    name_ko=breed_name_ko,
                    name_en=breed_name_en,
                    top10=is_top10,
                    size=size,
                    activity_level=activity_level,
                    temperament=temperament,
                    breed_group=breed_group,
                    image_url=image_url
                )
                session.add(new_breed)
                inserted += 1

            await session.commit()

        print(f"\n✅ breeds 테이블 데이터 갱신 완료!")
        print(f"   삽입: {inserted}개")

    except Exception as e:
        print(f"[ERROR] 작업 중 오류가 발생했습니다: {e}")
    finally:
        if tunnel and tunnel.is_active:
            tunnel.stop()
            print("SSH 터널 종료")

# ── 진입점 ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    asyncio.run(seed())
