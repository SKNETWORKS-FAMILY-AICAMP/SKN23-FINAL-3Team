# -*- coding: utf-8 -*-
"""
back/db/seeds/places_seed.py
-----------------------------
places 테이블에 장소 데이터를 적재하는 시드 스크립트.
"""
from __future__ import annotations

import os
import sys
import asyncio
import hashlib
import pandas as pd
import core.database

from sqlalchemy import text
from models.place import Place
from dotenv import load_dotenv
from core.config import settings
from sshtunnel import SSHTunnelForwarder

# ── 경로 설정: back/api 를 sys.path 에 추가 ────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))            # back/db/seeds/
_BACK_API = os.path.normpath(os.path.join(_HERE, "../../api"))  # back/api/
sys.path.insert(0, _BACK_API)

load_dotenv(os.path.normpath(os.path.join(_HERE, "../../../.env")))

CSV_PATH = os.path.normpath(os.path.join(_HERE, "../../../data/raw/한국문화정보원_전국_반려동물_동반_가능_문화시설_위치_데이터_20250324.csv"))

# embed_places.py의 카테고리 맵
CATEGORY_MAP = {
    "카페": "카페",
    "식당": "음식점",
    "펜션": "숙박",
    "호텔": "숙박",
    "여행지": "관광지",
    "박물관": "관광지",
    "미술관": "관광지",
    "문예회관": "관광지",
    "동물병원": "의료",
    "동물약국": "의료",
    "반려동물용품": "기타",
    "미용": "기타",
    "위탁관리": "기타",
}

# DB용 타입 코드 (12:관광지 14:문화시설 28:레포츠 32:숙박 38:쇼핑 39:음식점)
DB_TYPE_CD_MAP = {
    "관광지": "12",
    "문화시설": "14",
    "놀이터": "28",
    "공원": "12",
    "숙박": "32",
    "쇼핑": "38",
    "음식점": "39",
    "카페": "39",
    "의료": "14",
    "기타": "14"
}

def map_category(row):
    cat3 = str(row["카테고리3"]).strip()
    name = str(row["시설명"])

    if cat3 == "여행지":
        if "놀이터" in name:
            return "놀이터"
        elif "공원" in name:
            return "공원"
        else:
            return "관광지"

    return CATEGORY_MAP.get(cat3, "기타")


def load_and_filter(csv_path: str) -> pd.DataFrame:
    print("CSV 로드 중...")
    df = pd.read_csv(csv_path, encoding="utf-8")
    print(f"원본 데이터: {len(df)}개")

    # 반려동물 동반 가능한 곳만 필터링
    df = df[df["반려동물 동반 가능정보"] == "Y"]
    print(f"반려동물 동반 가능 필터링 후: {len(df)}개")

    # 위경도 범위 검증 (강원도 북부 포함)
    df = df[(df["위도"].between(33, 38.7)) & (df["경도"].between(124, 132))]
    print(f"위경도 범위 검증 후: {len(df)}개")

    # 도로명주소 null → 지번주소로 대체
    df["주소"] = df["도로명주소"].fillna(df["지번주소"])

    # 필수 필드 누락 제거
    df = df.dropna(subset=["시설명", "주소"])
    print(f"필수 필드 누락 제거 후: {len(df)}개")

    # 앞뒤 공백, 개행문자 제거
    df["시설명"] = df["시설명"].str.strip().str.replace("\n", " ")
    df["주소"] = df["주소"].str.strip().str.replace("\n", " ")

    # 중복 데이터 제거 (시설명과 주소가 동일한 경우)
    df = df.drop_duplicates(subset=["시설명", "주소"], keep="first")
    print(f"중복 데이터 제거 후: {len(df)}개")

    # 위경도 소수점 7자리 (DB 스펙)
    df["위도"] = (df["위도"]).round(7)
    df["경도"] = (df["경도"]).round(7)

    # 시도명 추출 (city 필드용)
    df["city"] = df["시도 명칭"].fillna("").str.strip()

    # category 매핑
    df["category"] = df.apply(map_category, axis=1)

    # 전처리 필드들 null 치환
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
    category = row["category"]
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

    doc = f"{name}은 {city}에 위치한 {category} 장소로 반려견 동반이 가능하다."

    if size and size not in ["해당없음", "모두 가능", ""]:
        doc += f" 입장 가능 크기: {size}."
    if conditions and conditions not in ["해당없음", "제한사항 없음", ""]:
        doc += f" 이용 조건: {conditions}."
    if space:
        doc += f" {space}."
    if pet_only and pet_only not in ["해당없음", "Y", "N", ""]:
        doc += f" 반려동물 전용 정보: {pet_only}."
    if extra_fee and extra_fee not in ["없음", "해당없음", ""]:
        doc += f" 애견 동반 추가 요금: {extra_fee}."
    if parking and parking not in ["해당없음", "불가", ""]:
        doc += f" 주차 {parking}."
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
                
                # 유의미한 고유 ID (VARCHAR 20) 생성 (이름+주소 해시)
                # TourAPI가 아니므로 자체 고유 ID 생성 (CSV 데이터 소스)
                raw_id_str = f"{name}_{address}".encode('utf-8')
                content_id_hash = hashlib.md5(raw_id_str).hexdigest()[:20]
                
                category = row["category"]
                content_type_id = DB_TYPE_CD_MAP.get(category, "14")
                
                is_indoor = True if row["장소(실내) 여부"] == "Y" else False
                
                acmpy_psbl_cpam = row["입장 가능 동물 크기"]
                acmpy_need_mtr = row["반려동물 제한사항"]
                etc_info = f"운영시간: {row['운영시간']} / 휴무일: {row['휴무일']}"
                
                desc_extra = row["기본 정보_장소설명"] 
                description_doc = build_document(row)
                if desc_extra:
                    description_doc += f"\n[장소 정보] {desc_extra}"

                new_place = Place(
                    content_id=content_id_hash,
                    content_type_id=content_type_id,
                    name=name,
                    address=address,
                    tel=row["전화번호"] if row["전화번호"] else None,
                    latitude=row["위도"],
                    longitude=row["경도"],
                    is_indoor=is_indoor,
                    acmpy_type_cd="전구역" if row["장소(실외)여부"] == "Y" and is_indoor else "일부구역",
                    acmpy_psbl_cpam=acmpy_psbl_cpam if acmpy_psbl_cpam else None,
                    acmpy_need_mtr=acmpy_need_mtr if acmpy_need_mtr else None,
                    rela_poses_fclty="Y" if row["주차 가능여부"] and row["주차 가능여부"] not in ["불가", "해당없음", ""] else "N",
                    etc_acmpy_info=etc_info,
                    description=description_doc,
                )
                session.add(new_place)
                inserted += 1
                
                # 메모리 효율을 위해 1,000건 단위 commit
                if inserted % 1000 == 0:
                    await session.commit()
                    print(f"  {inserted}건 저장 완료...")

            # 남은 데이터 커밋
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
