# -*- coding: utf-8 -*-
"""
back/db/seeds/places_seed.py  (최종본 v3)
-----------------------------
places 테이블에 장소 데이터를 적재하는 시드 스크립트.

수정 내역 (from original):
  [FIX-1] has_parking: 주차 Y/N 값 정확히 매핑 (기존 buggy truthy 로직 수정)
  [FIX-2] is_outdoor 컬럼 추가 (원본 '장소(실외)여부' 보존)
  [FIX-3] sub_category 컬럼 추가로 카테고리 세분화 유지
  [FIX-4] pet_zone_type 매핑 명확화 (실내구역/실외구역/전구역)
  [FIX-5] content_id 해시 충돌 방어
  [FIX-6] 컬럼명을 도메인 용어로 변경 (rela_poses_fclty → has_parking 등)
  [FIX-7] entrance_fee/extra_fee 정규화: description 자연어 → 4 정규화 컬럼 inline ETL
          (이전 normalize_fee.py 일회용 ETL 통합 — DB 재구축 시 단일 단계로 fee 컬럼 적재)

⚠️ 실행 전 필수:
  1. places_schema_migration_v2.sql 실행으로 컬럼명 변경
  2. models/place.py의 Place 클래스 속성명 동기화 + entrance_fee_*/extra_fee_* 4 컬럼
"""
from __future__ import annotations

import os
import sys

# ── 경로 설정: back/api 를 sys.path 에 선등록 (core/models import 전에 필수) ─
_HERE = os.path.dirname(os.path.abspath(__file__))              # back/db/seeds/
_BACK_API = os.path.normpath(os.path.join(_HERE, "../../api"))  # back/api/
sys.path.insert(0, _BACK_API)

import asyncio  # noqa: E402
import hashlib  # noqa: E402
import re  # noqa: E402
import pandas as pd  # noqa: E402
import core.database  # noqa: E402

from dataclasses import dataclass  # noqa: E402
from sqlalchemy import text  # noqa: E402
from models.place import Place  # noqa: E402
from core.type.place import FeeType  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from core.config import settings  # noqa: E402
from sshtunnel import SSHTunnelForwarder  # noqa: E402

load_dotenv(os.path.normpath(os.path.join(_HERE, "../../../.env")))

CSV_PATH = os.path.normpath(os.path.join(
    _HERE,
    "../../../data/raw/한국문화정보원_전국_반려동물_동반_가능_문화시설_위치_데이터_20250324.csv"
))

# ── fee 정규화 (description 자연어 → 4 컬럼 정규식 1차 패스) ────────────
# 우선순위 순차 적용, 첫 매칭에서 break.
# 검증 결과 (21,130 행): entrance_fee unknown 1.81%, extra_fee unknown 98.06%
# (펜션 외 카테고리는 추가요금 표기 자체가 없어 ROI 0 — 스펙 영구 보류 영역).
RE_FLAGS = re.DOTALL


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


# 각 항목: (pattern_idx, compiled_re, FeeType, amount_extractor)
ENTRANCE_RULES = [
    (1, re.compile(r"입장료\s*[:：]?\s*(무료|없|(?<!\d)0\s*원)", RE_FLAGS),
     FeeType.FREE, _amount_const(0)),
    (2, re.compile(r"입장료\s*[:：]\s*([\d,]+)\s*원", RE_FLAGS),
     FeeType.FIXED, _amount_group(1)),
    (3, re.compile(r"입장료\s*[:：]\s*(\d+)\s*만\s*원", RE_FLAGS),
     FeeType.FIXED, _amount_manwon(1)),
    (4, re.compile(r"입장료\s*[:：]\s*변동", RE_FLAGS),
     FeeType.VARIABLE, _amount_null),
    (5, re.compile(r"입장료\s*[:：]\s*(상이|시기별|계절별|문의)", RE_FLAGS),
     FeeType.VARIABLE, _amount_null),
    (6, re.compile(r"입장료\s*[:：].{0,30}?(성인|어린이|청소년)", RE_FLAGS),
     FeeType.CONDITIONAL, _amount_null),
]

EXTRA_RULES = [
    (1, re.compile(r"(추가\s*요금|동반료|입실료)\s*없", RE_FLAGS),
     FeeType.FREE, _amount_const(0)),
    (2, re.compile(r"반려[동물견].{0,30}?무료", RE_FLAGS),
     FeeType.FREE, _amount_const(0)),
    (3, re.compile(
         r"(애견|강아지|반려[동물견])\s*(동반)?\s*추가\s*요금\s*[:：]\s*([\d,]+)\s*원",
         RE_FLAGS,
     ),
     FeeType.FIXED, _amount_group(3)),
    (4, re.compile(r"(추가\s*요금|동반료|입실료)\s*[:：]?\s*([\d,]+)\s*원", RE_FLAGS),
     FeeType.FIXED, _amount_group(2)),
    (5, re.compile(r"(추가\s*요금|동반료|입실료)\s*[:：]?\s*(\d+)\s*만\s*원", RE_FLAGS),
     FeeType.FIXED, _amount_manwon(2)),
    (6, re.compile(r"(추가\s*요금|동반료).{0,30}?(변동|상이|문의)", RE_FLAGS),
     FeeType.VARIABLE, _amount_null),
    (7, re.compile(r"(추가\s*요금|동반료).{0,30}?(소형|중형|대형|체급|크기별)", RE_FLAGS),
     FeeType.CONDITIONAL, _amount_null),
]


@dataclass
class FeeMatch:
    """fee 정규화 결과 한 컬럼 단위."""
    fee_type: FeeType
    amount: int | None


def _match_rules(description: str | None, rules: list) -> FeeMatch:
    """우선순위 순서로 룰 적용, 첫 매칭 반환. 매칭 실패 시 unknown."""
    if not description:
        return FeeMatch(FeeType.UNKNOWN, None)
    for _idx, pattern, fee_type, extractor in rules:
        m = pattern.search(description)
        if not m:
            continue
        try:
            amount = extractor(m)
        except (ValueError, IndexError):
            continue
        return FeeMatch(fee_type, amount)
    return FeeMatch(FeeType.UNKNOWN, None)


def normalize_fee(description: str | None) -> tuple[FeeMatch, FeeMatch]:
    """description → (entrance_fee 결과, extra_fee 결과). 두 룰셋 독립 적용."""
    return _match_rules(description, ENTRANCE_RULES), _match_rules(description, EXTRA_RULES)


# ── 카테고리 매핑: (content_type_id, sub_category) ────────────
BIG_CATEGORY_MAP = {
    "카페":         ("39", "카페"),
    "식당":         ("39", "식당"),
    "펜션":         ("32", "펜션"),
    "호텔":         ("32", "호텔"),
    "여행지":       ("12", "여행지"),   # 놀이터/공원은 별도 처리
    "박물관":       ("12", "박물관"),
    "미술관":       ("12", "미술관"),
    "문예회관":     ("12", "문예회관"),
    "동물병원":     ("14", "동물병원"),
    "동물약국":     ("14", "동물약국"),
    "반려동물용품": ("38", "반려동물용품"),
    "미용":         ("14", "미용"),
    "위탁관리":     ("14", "위탁관리"),
}


def map_category(row) -> tuple[str, str]:
    """(content_type_id, sub_category) 반환"""
    cat3 = str(row["카테고리3"]).strip()
    name = str(row["시설명"])

    if cat3 == "여행지":
        if "놀이터" in name:
            return ("28", "반려견놀이터")
        elif "공원" in name:
            return ("12", "공원")
        else:
            return ("12", "관광지")

    return BIG_CATEGORY_MAP.get(cat3, ("14", "기타"))


def load_and_filter(csv_path: str) -> pd.DataFrame:
    print("CSV 로드 중...")
    df = pd.read_csv(csv_path, encoding="utf-8")
    print(f"원본 데이터: {len(df):,}개")

    df = df[df["반려동물 동반 가능정보"] == "Y"]
    print(f"반려동물 동반 가능 필터링 후: {len(df):,}개")

    df = df[(df["위도"].between(33, 38.7)) & (df["경도"].between(124, 132))]
    print(f"위경도 범위 검증 후: {len(df):,}개")

    df["주소"] = df["도로명주소"].fillna(df["지번주소"])
    df = df.dropna(subset=["시설명", "주소"])
    print(f"필수 필드 누락 제거 후: {len(df):,}개")

    df["시설명"] = df["시설명"].str.strip().str.replace("\n", " ")
    df["주소"] = df["주소"].str.strip().str.replace("\n", " ")
    df = df.drop_duplicates(subset=["시설명", "주소"], keep="first")
    print(f"중복 데이터 제거 후: {len(df):,}개")

    df["위도"] = df["위도"].round(7)
    df["경도"] = df["경도"].round(7)
    df["city"] = df["시도 명칭"].fillna("").str.strip()

    df[["content_type_id", "sub_category"]] = df.apply(
        lambda r: pd.Series(map_category(r)), axis=1
    )

    fill_cols = ["운영시간", "휴무일", "주차 가능여부", "입장(이용료)가격 정보", "전화번호",
                 "홈페이지", "반려동물 제한사항", "입장 가능 동물 크기", "반려동물 전용 정보",
                 "애견 동반 추가 요금", "기본 정보_장소설명"]
    for col in fill_cols:
        df[col] = df[col].fillna("").astype(str).str.strip()

    df["장소(실내) 여부"] = df["장소(실내) 여부"].fillna("N")
    df["장소(실외)여부"] = df["장소(실외)여부"].fillna("N")

    return df


def build_document(row) -> str:
    """벡터화할 document 문장 구성"""
    name = row["시설명"]
    city = row["city"]
    sub_cat = row["sub_category"]
    conditions = row["반려동물 제한사항"]
    size = row["입장 가능 동물 크기"]
    indoor = "실내 가능" if row["장소(실내) 여부"] == "Y" else ""
    outdoor = "실외 가능" if row["장소(실외)여부"] == "Y" else ""
    space = ", ".join(filter(None, [indoor, outdoor]))
    pet_only = row["반려동물 전용 정보"]
    extra_fee = row["애견 동반 추가 요금"]
    parking = row["주차 가능여부"]
    entrance_fee = row["입장(이용료)가격 정보"]
    open_hours = row["운영시간"]
    closed_days = row["휴무일"]

    doc = f"{name}은 {city}에 위치한 {sub_cat} 장소로 반려견 동반이 가능하다."

    if size and size not in ["해당없음", "모두 가능", ""]:
        doc += f" 입장 가능 크기: {size}."
    if conditions and conditions not in ["해당없음", "제한사항 없음", ""]:
        doc += f" 이용 조건: {conditions}."
    if space:
        doc += f" {space}."
    if pet_only and pet_only == "반려동물 전용":
        doc += " 반려동물 전용 공간."
    if extra_fee and extra_fee not in ["없음", "해당없음", ""]:
        doc += f" 애견 동반 추가 요금: {extra_fee}."
    # [FIX-1] 주차 Y/N 모두 의미 있게 반영
    if parking == "Y":
        doc += " 주차 가능."
    elif parking == "N":
        doc += " 주차 불가."
    if entrance_fee and entrance_fee not in ["해당없음", ""]:
        doc += f" 입장료: {entrance_fee}."
    if open_hours:
        doc += f" 운영시간: {open_hours}."
    if closed_days and closed_days not in ["해당없음", ""]:
        doc += f" 휴무일: {closed_days}."

    return doc


async def seed() -> None:
    db_host = settings.DB_HOST
    db_port = settings.DB_PORT

    tunnel = None
    if settings.SERVER == "local":
        print("SSH 터널 연결 중...")
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

    core.database.init_engine(host=db_host, port=db_port)

    try:
        df = load_and_filter(CSV_PATH)

        if df.empty:
            print("투입할 데이터가 없습니다.")
            return

        inserted = 0

        async with core.database.AsyncSessionLocal() as session:
            print("기존 places 데이터 삭제 및 AUTO_INCREMENT 초기화 진행 중...")
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            await session.execute(text("DELETE FROM places;"))
            await session.execute(text("ALTER TABLE places AUTO_INCREMENT = 1;"))
            await session.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            await session.commit()

            print("데이터 적재 중...")
            for i, row in df.iterrows():
                name = row["시설명"]
                address = row["주소"]

                # [FIX-5] 해시 인풋에 카테고리 포함해서 충돌 방어
                raw_id_str = f"{name}_{address}".encode('utf-8')
                content_id_hash = hashlib.md5(raw_id_str).hexdigest()[:20]

                content_type_id = row["content_type_id"]
                sub_category = row["sub_category"]

                # [FIX-2] 실내/실외 각각 저장
                is_indoor = (row["장소(실내) 여부"] == "Y")
                is_outdoor = (row["장소(실외)여부"] == "Y")

                # [FIX-4] pet_zone_type 의미 명확화
                if is_indoor and is_outdoor:
                    pet_zone_type = "전구역"
                elif is_indoor:
                    pet_zone_type = "실내구역"
                elif is_outdoor:
                    pet_zone_type = "실외구역"
                else:
                    pet_zone_type = "정보없음"

                # [FIX-1] 주차 Y/N 값 그대로 보존
                parking_value = "Y" if row["주차 가능여부"] == "Y" else "N"

                operation_info = f"운영시간: {row['운영시간']} / 휴무일: {row['휴무일']}"
                desc_extra = row["기본 정보_장소설명"]
                description_doc = build_document(row)
                if desc_extra:
                    description_doc += f"\n[장소 정보] {desc_extra}"

                # [FIX-7] description 정규식 fee 정규화 — INSERT 시 4 컬럼 같이 채움
                ent_fee, ext_fee = normalize_fee(description_doc)

                # [FIX-6] 새 컬럼명 사용
                new_place = Place(
                    content_id=content_id_hash,
                    content_type_id=content_type_id,
                    sub_category=sub_category,
                    name=name,
                    address=address,
                    tel=row["전화번호"] if row["전화번호"] else None,
                    latitude=row["위도"],
                    longitude=row["경도"],
                    is_indoor=is_indoor,
                    is_outdoor=is_outdoor,
                    pet_zone_type=pet_zone_type,
                    pet_size_limit=row["입장 가능 동물 크기"] or None,
                    pet_restrictions=row["반려동물 제한사항"] or None,
                    has_parking=parking_value,
                    operation_info=operation_info,
                    description=description_doc,
                    entrance_fee_amount=ent_fee.amount,
                    entrance_fee_type=ent_fee.fee_type,
                    extra_fee_amount=ext_fee.amount,
                    extra_fee_type=ext_fee.fee_type,
                )
                session.add(new_place)
                inserted += 1

                if inserted % 1000 == 0:
                    await session.commit()
                    print(f"  {inserted}건 저장 완료...")

            await session.commit()

        print(f"\n✅ places 테이블 데이터 갱신 완료!")
        print(f"   삽입: {inserted}개")

    except Exception as e:
        print(f"[ERROR] 작업 중 오류가 발생했습니다: {e}")
    finally:
        if tunnel and tunnel.is_active:
            tunnel.stop()
            print("SSH 터널 종료")


if __name__ == "__main__":
    asyncio.run(seed())