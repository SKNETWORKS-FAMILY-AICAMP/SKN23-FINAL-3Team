# -*- coding: utf-8 -*-
"""
data/raw/tour_api_places_filtered.csv를 RDB places 테이블 컬럼에 맞춰 증분 적재하는 스크립트입니다.

주의사항:
- 기존 places 데이터를 삭제하지 않습니다.
- content_id UNIQUE KEY를 기준으로 새 데이터는 추가하고, 기존 데이터는 갱신합니다.
- CSV 컬럼을 그대로 넣지 않고 RDB places 컬럼 구조에 맞게 변환합니다.
- CSV의 image_url, homepage, pet_facility는 현재 RDB places 컬럼에 없으므로 적재하지 않습니다.

프로젝트 루트에서 실행 예시:
    python back\\data\\scripts\\places_seed_new.py --dry-run
    python back\\data\\scripts\\places_seed_new.py --execute
    python back\\data\\scripts\\places_seed_new.py --execute --limit 1000
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import sys
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

import pandas as pd


HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, "../../.."))
BACK_API = os.path.normpath(os.path.join(REPO_ROOT, "back/api"))
sys.path.insert(0, BACK_API)


CSV_PATH = os.path.join(REPO_ROOT, "data/raw/tour_api_places_filtered.csv")
DEFAULT_BATCH_SIZE = 500

CONTENT_TYPE_TO_CATEGORY = {
    "12": "관광지",
    "14": "문화시설",
    "28": "레포츠",
    "32": "숙박",
    "38": "쇼핑",
    "39": "식당",
}

# 기존 places_seed.py BIG_CATEGORY_MAP (16종) 정합 — site place_service.py 의
# sub_category 분기 (`{"반려동물용품","동물병원","동물약국","미용","위탁관리"}`,
# OUTING_SUBCATEGORIES, DEPRIORITIZED_SUBCATEGORIES) 와 매칭 유지.
# 매칭 우선순위: 더 구체적인 규칙이 먼저 (예: "위탁관리" ▶ "호텔", "미술관" ▶ "박물관").
CATEGORY_KEYWORD_RULES = [
    ("반려견놀이터", ("놀이터", "애견놀이터", "반려견 놀이터", "반려견놀이터", "댕댕이놀이터")),
    ("동물병원", ("동물병원", "동물의료센터", "동물메디컬센터", "동물클리닉", "수의과")),
    ("동물약국", ("동물약국",)),
    ("반려동물용품", ("반려동물용품", "애견용품", "펫숍", "펫샵", "반려동물샵", "댕댕이숍")),
    ("미용", ("애견미용", "반려동물미용", "펫미용")),
    # "위탁관리" 는 "호텔" 보다 먼저 — "애견호텔" / "펫호텔" 이 일반 호텔 룰에 잡히지 않도록.
    ("위탁관리", ("애견호텔", "펫호텔", "위탁", "도그유치원", "강아지유치원", "댕댕이유치원")),
    ("미술관", ("미술관",)),
    ("문예회관", ("문예회관", "예술회관", "문화회관", "아트홀", "공연장")),
    ("박물관", ("박물관", "과학관", "갤러리", "전시관", "기념관")),
    ("카페", ("카페", "베이커리", "젤라또", "디저트", "커피", "로스터리")),
    ("식당", ("식당", "레스토랑", "한정식", "분식", "고깃집", "갈빗집")),
    ("펜션", ("펜션", "빌라", "풀빌라", "글램핑", "카라반")),
    ("호텔", ("호텔", "리조트", "스위트", "콘도")),
    ("공원", ("공원", "수변", "정원", "숲", "유원지", "둘레길", "산책로", "탐방로", "휴양림")),
]


# ── fee 정규화 (description 자연어 → 4 컬럼 정규식 1차 패스) ────────────
# 기존 places_seed.py [FIX-7] 정합. 우선순위 순차 적용, 첫 매칭에서 break.
# FeeType enum 은 string value 만 사용 (모델 import 회피 — DB 적재 시 SQL 직접
# 사용이라 Python enum 객체 불필요).
_RE_FLAGS = re.DOTALL


def _amount_const(value: int):
    def _impl(_match: re.Match) -> int:
        return value
    return _impl


def _amount_group(idx: int):
    def _impl(match: re.Match) -> int:
        raw = match.group(idx).replace(",", "").strip()
        return int(raw)
    return _impl


def _amount_manwon(idx: int):
    def _impl(match: re.Match) -> int:
        raw = match.group(idx).replace(",", "").strip()
        return int(raw) * 10000
    return _impl


def _amount_null(_match: re.Match) -> None:
    return None


# (compiled_re, fee_type_value, amount_extractor)
_ENTRANCE_RULES = [
    (re.compile(r"입장료\s*[:：]?\s*(무료|없|(?<!\d)0\s*원)", _RE_FLAGS), "free", _amount_const(0)),
    (re.compile(r"입장료\s*[:：]\s*([\d,]+)\s*원", _RE_FLAGS), "fixed", _amount_group(1)),
    (re.compile(r"입장료\s*[:：]\s*(\d+)\s*만\s*원", _RE_FLAGS), "fixed", _amount_manwon(1)),
    (re.compile(r"입장료\s*[:：]\s*변동", _RE_FLAGS), "variable", _amount_null),
    (re.compile(r"입장료\s*[:：]\s*(상이|시기별|계절별|문의)", _RE_FLAGS), "variable", _amount_null),
    (re.compile(r"입장료\s*[:：].{0,30}?(성인|어린이|청소년)", _RE_FLAGS), "conditional", _amount_null),
]

_EXTRA_RULES = [
    (re.compile(r"(추가\s*요금|동반료|입실료)\s*없", _RE_FLAGS), "free", _amount_const(0)),
    (re.compile(r"반려[동물견].{0,30}?무료", _RE_FLAGS), "free", _amount_const(0)),
    (re.compile(
        r"(애견|강아지|반려[동물견])\s*(동반)?\s*추가\s*요금\s*[:：]\s*([\d,]+)\s*원", _RE_FLAGS,
    ), "fixed", _amount_group(3)),
    (re.compile(r"(추가\s*요금|동반료|입실료)\s*[:：]?\s*([\d,]+)\s*원", _RE_FLAGS), "fixed", _amount_group(2)),
    (re.compile(r"(추가\s*요금|동반료|입실료)\s*[:：]?\s*(\d+)\s*만\s*원", _RE_FLAGS), "fixed", _amount_manwon(2)),
    (re.compile(r"(추가\s*요금|동반료).{0,30}?(변동|상이|문의)", _RE_FLAGS), "variable", _amount_null),
    (re.compile(r"(추가\s*요금|동반료).{0,30}?(소형|중형|대형|체급|크기별)", _RE_FLAGS), "conditional", _amount_null),
]


@dataclass
class FeeMatch:
    """fee 정규화 결과 한 컬럼 단위."""
    fee_type: str  # "free" | "fixed" | "variable" | "conditional" | "unknown"
    amount: int | None


def _match_fee_rules(description: str | None, rules: list) -> FeeMatch:
    """우선순위 순서로 룰 적용, 첫 매칭 반환. 매칭 실패 시 unknown."""
    if not description:
        return FeeMatch("unknown", None)
    for pattern, fee_type, extractor in rules:
        m = pattern.search(description)
        if not m:
            continue
        try:
            amount = extractor(m)
        except (ValueError, IndexError):
            continue
        return FeeMatch(fee_type, amount)
    return FeeMatch("unknown", None)


def normalize_fee(description: str | None) -> tuple[FeeMatch, FeeMatch]:
    """description → (entrance_fee 결과, extra_fee 결과). 두 룰셋 독립 적용."""
    return (
        _match_fee_rules(description, _ENTRANCE_RULES),
        _match_fee_rules(description, _EXTRA_RULES),
    )


def clean(value: Any) -> str | None:
    """빈 문자열, NaN, null 계열 값을 DB NULL로 넣기 위해 None으로 정리합니다."""
    if value is None or pd.isna(value):
        return None
    value = str(value).strip()
    if not value:
        return None
    if value.lower() in {"nan", "none", "null"}:
        return None
    return value


def truncate(value: str | None, length: int) -> str | None:
    """RDB varchar 길이를 넘지 않도록 문자열을 자릅니다."""
    if value is None:
        return None
    return value[:length]


def parse_decimal(value: Any, places: int = 7) -> Decimal | None:
    """lat/lng 값을 RDB decimal(10,7)에 맞게 반올림합니다."""
    value = clean(value)
    if value is None:
        return None
    try:
        quant = Decimal("1").scaleb(-places)
        return Decimal(value).quantize(quant)
    except (InvalidOperation, ValueError):
        return None


def parse_parking(value: Any) -> str:
    """CSV parking 값을 RDB has_parking enum('Y','N') 값으로 변환합니다.

    기존 places_seed.py 정합 — 매칭 실패 시 "N" fallback (NULL 미사용).
    """
    value = clean(value)
    if value is None:
        return "N"
    if value in {"가능", "Y", "있음", "주차 가능"}:
        return "Y"
    if value in {"불가", "N", "없음", "주차 불가"}:
        return "N"
    return "N"


def parse_indoor_outdoor(pet_acmpy_type: Any) -> tuple[int, int]:
    """pet_acmpy_type 에서 실내/실외 동반 가능 여부를 추정합니다.

    기존 places_seed.py 정합 — 매칭 실패 시 0 (False) fallback (NULL 미사용).
    site place_service.py:630 의 `is_indoor == obj["is_indoor"]` 쿼리가 NULL
    행을 누락하므로 0 강제로 일관성 유지.
    """
    value = clean(pet_acmpy_type)
    if value is None:
        return 0, 0

    if "전구역" in value:
        return 1, 1

    is_indoor = 1 if "실내" in value else 0
    is_outdoor = 1 if ("실외" in value or "야외" in value) else 0
    return is_indoor, is_outdoor


def parse_pet_zone_type(pet_acmpy_type: Any, is_indoor: int, is_outdoor: int) -> str:
    """pet_acmpy_type 을 RDB pet_zone_type 문자열로 변환합니다.

    기존 places_seed.py 정합 — 매칭 실패 시 "정보없음" fallback. CSV 의
    "일부구역" 표현은 추가 분기 (기존 4종 → 5종 확장, site 분기 미영향).
    """
    value = clean(pet_acmpy_type)
    if is_indoor == 1 and is_outdoor == 1:
        return "전구역"
    if is_indoor == 1:
        return "실내구역"
    if is_outdoor == 1:
        return "실외구역"
    if value and "일부구역" in value:
        return "일부구역"
    return "정보없음"


def map_sub_category(row_or_content_type_id: Any) -> str | None:
    """장소명 키워드를 우선 보고, 없으면 content_type_id 대분류로 변환합니다."""
    if isinstance(row_or_content_type_id, pd.Series):
        search_text = " ".join(
            value
            for value in [
                clean(row_or_content_type_id.get("name")),
            ]
            if value
        )
        for category, keywords in CATEGORY_KEYWORD_RULES:
            if any(keyword in search_text for keyword in keywords):
                return category

        content_type_id = row_or_content_type_id.get("content_type_id")
    else:
        content_type_id = row_or_content_type_id

    value = clean(content_type_id)
    if value is None:
        return None
    return CONTENT_TYPE_TO_CATEGORY.get(value)


def join_nonempty(*parts: Any, sep: str = " / ") -> str | None:
    """여러 CSV 컬럼을 빈 값 제외 후 하나의 문자열로 합칩니다."""
    values = [clean(part) for part in parts]
    values = [value for value in values if value]
    return sep.join(values) if values else None


def build_operation_info(row: pd.Series) -> str:
    """open_hours·closed_days 를 RDB operation_info 로 합칩니다.

    기존 places_seed.py 의 고정 형식 정합 —
    `f"운영시간: {open_hours} / 휴무일: {closed_days}"` 빈값 포함 항상 유지.
    """
    open_hours = clean(row.get("open_hours")) or ""
    closed_days = clean(row.get("closed_days")) or ""
    return f"운영시간: {open_hours} / 휴무일: {closed_days}"


def build_pet_restrictions(row: pd.Series) -> str | None:
    """pet_need 와 pet_etc_info 를 RDB pet_restrictions 로 합칩니다."""
    return join_nonempty(row.get("pet_need"), row.get("pet_etc_info"))


def build_document(
    row: pd.Series,
    sub_category: str | None,
    is_indoor: int,
    is_outdoor: int,
    has_parking: str,
    pet_restrictions: str | None,
) -> str:
    """벡터 임베딩 source 로 사용될 자연어 prose 합성.

    기존 places_seed.py `build_document` 정합 — ChromaDB 임베딩 품질 일관성 유지.
    "반려견 동반 가능", "주차 가능/불가", "실내/실외 가능" 등 강한 키워드를 본문
    에 명시 포함 → site place_service.py 의 RAG 검색 매칭 점수 보존.

    overview 가 있으면 마지막에 `[장소 정보]` 블록으로 append.
    """
    name = clean(row.get("name")) or ""
    city = clean(row.get("city")) or ""
    pet_size = clean(row.get("pet_acmpy_animal"))
    open_hours = clean(row.get("open_hours"))
    closed_days = clean(row.get("closed_days"))
    overview = clean(row.get("overview"))

    indoor_str = "실내 가능" if is_indoor == 1 else ""
    outdoor_str = "실외 가능" if is_outdoor == 1 else ""
    space = ", ".join(filter(None, [indoor_str, outdoor_str]))

    cat = sub_category or "장소"
    location = city or "한국"
    doc = f"{name}은 {location}에 위치한 {cat} 장소로 반려견 동반이 가능하다."

    if pet_size and pet_size not in ("해당없음", "모두 가능"):
        doc += f" 입장 가능 크기: {pet_size}."
    if pet_restrictions and pet_restrictions not in ("해당없음", "제한사항 없음"):
        doc += f" 이용 조건: {pet_restrictions}."
    if space:
        doc += f" {space}."
    # 주차 — 기존 시드 [FIX-1] 정합 (Y/N 모두 의미 있게 반영)
    if has_parking == "Y":
        doc += " 주차 가능."
    elif has_parking == "N":
        doc += " 주차 불가."
    if open_hours:
        doc += f" 운영시간: {open_hours}."
    if closed_days and closed_days not in ("해당없음", ""):
        doc += f" 휴무일: {closed_days}."

    if overview:
        doc += f"\n[장소 정보] {overview}"
    return doc


def row_to_params(row: pd.Series) -> dict[str, Any] | None:
    """CSV 한 row 를 RDB places INSERT 파라미터로 변환합니다.

    기존 places_seed.py 형식 정합 — is_indoor/is_outdoor·has_parking·
    pet_zone_type 모두 NULL 미사용 (0/N/"정보없음" fallback). description 은
    build_document prose 합성 + overview append. fee 4 컬럼은 description
    정규화로 자동 추출.
    """
    content_id = truncate(clean(row.get("content_id")), 20)
    content_type_id = truncate(clean(row.get("content_type_id")), 5)
    name = truncate(clean(row.get("name")), 200)

    if not content_id or not content_type_id or not name:
        return None

    sub_category = truncate(map_sub_category(row), 30)
    is_indoor, is_outdoor = parse_indoor_outdoor(row.get("pet_acmpy_type"))
    pet_zone_type = parse_pet_zone_type(row.get("pet_acmpy_type"), is_indoor, is_outdoor)
    has_parking = parse_parking(row.get("parking"))
    pet_restrictions = build_pet_restrictions(row)
    description = build_document(row, sub_category, is_indoor, is_outdoor, has_parking, pet_restrictions)
    entrance_fee, extra_fee = normalize_fee(description)

    return {
        "content_id": content_id,
        "content_type_id": content_type_id,
        "sub_category": sub_category,
        "name": name,
        "address": truncate(clean(row.get("address")), 300),
        "tel": truncate(clean(row.get("tel")), 50),
        "latitude": parse_decimal(row.get("lat")),
        "longitude": parse_decimal(row.get("lng")),
        "is_indoor": is_indoor,
        "is_outdoor": is_outdoor,
        "pet_zone_type": truncate(pet_zone_type, 50),
        "pet_size_limit": truncate(clean(row.get("pet_acmpy_animal")), 300),
        "pet_restrictions": truncate(pet_restrictions, 300),
        "has_parking": has_parking,
        "operation_info": build_operation_info(row),
        "description": description,
        "entrance_fee_amount": entrance_fee.amount,
        "entrance_fee_type": entrance_fee.fee_type,
        "extra_fee_amount": extra_fee.amount,
        "extra_fee_type": extra_fee.fee_type,
    }


UPSERT_SQL = """
    INSERT INTO places (
        content_id,
        content_type_id,
        sub_category,
        name,
        address,
        tel,
        latitude,
        longitude,
        is_indoor,
        is_outdoor,
        pet_zone_type,
        pet_size_limit,
        pet_restrictions,
        has_parking,
        operation_info,
        description,
        entrance_fee_amount,
        entrance_fee_type,
        extra_fee_amount,
        extra_fee_type
    ) VALUES (
        :content_id,
        :content_type_id,
        :sub_category,
        :name,
        :address,
        :tel,
        :latitude,
        :longitude,
        :is_indoor,
        :is_outdoor,
        :pet_zone_type,
        :pet_size_limit,
        :pet_restrictions,
        :has_parking,
        :operation_info,
        :description,
        :entrance_fee_amount,
        :entrance_fee_type,
        :extra_fee_amount,
        :extra_fee_type
    )
    ON DUPLICATE KEY UPDATE
        content_type_id = VALUES(content_type_id),
        sub_category = VALUES(sub_category),
        name = VALUES(name),
        address = VALUES(address),
        tel = VALUES(tel),
        latitude = VALUES(latitude),
        longitude = VALUES(longitude),
        is_indoor = VALUES(is_indoor),
        is_outdoor = VALUES(is_outdoor),
        pet_zone_type = VALUES(pet_zone_type),
        pet_size_limit = VALUES(pet_size_limit),
        pet_restrictions = VALUES(pet_restrictions),
        has_parking = VALUES(has_parking),
        operation_info = VALUES(operation_info),
        description = VALUES(description),
        entrance_fee_amount = VALUES(entrance_fee_amount),
        entrance_fee_type = VALUES(entrance_fee_type),
        extra_fee_amount = VALUES(extra_fee_amount),
        extra_fee_type = VALUES(extra_fee_type),
        updated_at = CURRENT_TIMESTAMP
"""


def load_rows(csv_path: str, limit: int | None) -> list[dict[str, Any]]:
    """CSV를 읽고 RDB 적재 가능한 파라미터 목록으로 변환합니다."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str)
    if limit:
        df = df.head(limit)

    rows = []
    skipped = 0
    for _, row in df.iterrows():
        params = row_to_params(row)
        if params is None:
            skipped += 1
            continue
        rows.append(params)

    print(f"선택된 CSV row 수: {len(df):,}")
    print(f"적재 가능한 row 수: {len(rows):,}")
    print(f"필수값 누락으로 제외된 row 수: {skipped:,}")
    return rows


async def upsert_rows(rows: list[dict[str, Any]], batch_size: int) -> None:
    """변환된 row를 places 테이블에 배치 단위로 upsert합니다."""
    import core.database
    from sqlalchemy import text

    async with core.database.AsyncSessionLocal() as session:
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            await session.execute(text(UPSERT_SQL), batch)
            await session.commit()
            print(f"적재 완료: {min(start + batch_size, len(rows)):,}/{len(rows):,}")


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=CSV_PATH, help="적재할 관광공사 raw CSV 경로입니다.")
    parser.add_argument("--limit", type=int, help="앞에서부터 지정한 개수만 처리합니다.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="DB 배치 적재 단위입니다.")
    parser.add_argument("--dry-run", action="store_true", help="DB에 쓰지 않고 변환 결과만 확인합니다.")
    parser.add_argument("--execute", action="store_true", help="실제로 RDB에 적재합니다.")
    args = parser.parse_args()

    if args.dry_run and args.execute:
        raise SystemExit("--dry-run과 --execute 중 하나만 사용할 수 있습니다.")
    if not args.dry_run and not args.execute:
        args.dry_run = True

    rows = load_rows(args.csv, args.limit)
    if not rows:
        print("처리할 row가 없습니다.")
        return

    print("변환 샘플 row:")
    for key in sorted(rows[0]):
        print(f"  {key}: {rows[0][key]}")

    if args.dry_run:
        print("Dry run 완료. 실제 RDB에 적재하려면 --execute 옵션으로 다시 실행하세요.")
        return

    from dotenv import load_dotenv
    from sshtunnel import SSHTunnelForwarder
    import core.database
    from core.config import settings

    load_dotenv(os.path.join(REPO_ROOT, ".env"))

    db_host = settings.DB_HOST
    db_port = settings.DB_PORT
    tunnel = None

    if settings.SERVER == "local":
        tunnel = SSHTunnelForwarder(
            (settings.SSH_HOST, settings.SSH_PORT),
            ssh_username=settings.SSH_USER,
            ssh_pkey=os.path.expanduser(settings.SSH_PKEY),
            remote_bind_address=(settings.DB_HOST, settings.DB_PORT),
            local_bind_address=("127.0.0.1",),
        )
        tunnel.start()
        db_host = "127.0.0.1"
        db_port = tunnel.local_bind_port
        print(f"SSH 터널 연결 완료: 127.0.0.1:{db_port}")

    try:
        core.database.init_engine(host=db_host, port=db_port)
        await upsert_rows(rows, args.batch_size)
    finally:
        await core.database.close_db()
        if tunnel and tunnel.is_active:
            tunnel.stop()
            print("SSH 터널 종료 완료.")


if __name__ == "__main__":
    asyncio.run(main())
