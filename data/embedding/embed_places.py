import os
import chromadb
import pandas as pd

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# ── 설정 ──────────────────────────────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(__file__), "../data/raw/한국문화정보원_전국_반려동물_동반_가능_문화시설_위치_데이터_20250324.csv")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../chroma_db")
COLLECTION_NAME = "dog_places"
MODEL_NAME = "jhgan/ko-sroberta-multitask"

# ── 카테고리3 → category 매핑 ─────────────────────────────────
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
    """CSV 로드 및 전처리"""
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

    # 위경도 소수점 4자리 통일
    df["위도"] = df["위도"].round(4)
    df["경도"] = df["경도"].round(4)

    # 시도명 추출 (city 필드용)
    df["city"] = df["시도 명칭"].fillna("").str.strip()

    # category 매핑 (공원/놀이터 시설명 기준 분류 포함)
    df["category"] = df.apply(map_category, axis=1)

    # 운영시간 null → 빈 문자열
    df["운영시간"] = df["운영시간"].fillna("").str.strip()

    # 휴무일 null → 빈 문자열
    df["휴무일"] = df["휴무일"].fillna("").str.strip()

    # 주차 가능여부 null → 빈 문자열
    df["주차 가능여부"] = df["주차 가능여부"].fillna("").str.strip()

    # 입장(이용료)가격 정보 null → 빈 문자열
    df["입장(이용료)가격 정보"] = df["입장(이용료)가격 정보"].fillna("").str.strip()

    # 전화번호 null → 빈 문자열
    df["전화번호"] = df["전화번호"].fillna("").str.strip()

    # 홈페이지 null → 빈 문자열
    df["홈페이지"] = df["홈페이지"].fillna("").str.strip()

    # 반려동물 제한사항 null → 빈 문자열
    df["반려동물 제한사항"] = df["반려동물 제한사항"].fillna("").str.strip()

    # 입장 가능 동물 크기 null → 빈 문자열
    df["입장 가능 동물 크기"] = df["입장 가능 동물 크기"].fillna("").str.strip()

    # 실내/실외 여부 null → N
    df["장소(실내) 여부"] = df["장소(실내) 여부"].fillna("N")
    df["장소(실외)여부"] = df["장소(실외)여부"].fillna("N")

    # 반려동물 전용 정보 null → 빈 문자열
    df["반려동물 전용 정보"] = df["반려동물 전용 정보"].fillna("").str.strip()

    # 애견 동반 추가 요금 null → 빈 문자열
    df["애견 동반 추가 요금"] = df["애견 동반 추가 요금"].fillna("").str.strip()

    return df


def build_document(row) -> str:
    """벡터화할 document 문장 구성 — 유사도 검색 품질을 위해 모든 조건 포함"""
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
    parking = str(row["주차 가능여부"]) if row["주차 가능여부"] else ""
    entrance_fee = str(row["입장(이용료)가격 정보"]) if row["입장(이용료)가격 정보"] else ""
    open_hours = str(row["운영시간"]) if row["운영시간"] else ""
    closed_days = str(row["휴무일"]) if row["휴무일"] else ""

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


def embed_and_store(df: pd.DataFrame):
    """임베딩 생성 및 ChromaDB 저장"""

    # 모델 로드
    print(f"\n임베딩 모델 로드 중: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("모델 로드 완료!")

    # ChromaDB 초기화
    print(f"\nChromaDB 초기화: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # 기존 컬렉션 삭제 후 재생성
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 삭제")
    except:
        pass

    collection = client.create_collection(
        COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    print(f"'{COLLECTION_NAME}' 컬렉션 생성 완료")

    # 배치 처리 (메모리 효율)
    BATCH_SIZE = 500
    total = len(df)
    print(f"\n총 {total}개 데이터 적재 시작...")

    for i in range(0, total, BATCH_SIZE):
        batch = df.iloc[i:i + BATCH_SIZE]

        documents = [build_document(row) for _, row in batch.iterrows()]
        ids = [f"place_{i + j}" for j in range(len(batch))]

        # 임베딩 생성
        embeddings = model.encode(documents, show_progress_bar=False).tolist()

        # metadata 구성
        metadatas = []
        for _, row in batch.iterrows():
            conditions = row["반려동물 제한사항"]
            size = row["입장 가능 동물 크기"]
            extra_fee = row["애견 동반 추가 요금"]

            metadatas.append({
                "name": str(row["시설명"]),
                "address": str(row["주소"]),
                "category": str(row["category"]),
                "city": str(row["city"]),
                "lat": float(row["위도"]),
                "lng": float(row["경도"]),
                "open_hours": str(row["운영시간"]) if row["운영시간"] else "운영 시간 미제공 · 방문 전 문의 권장",
                "closed_days": str(row["휴무일"]) if row["휴무일"] else "",
                "parking": str(row["주차 가능여부"]) if row["주차 가능여부"] else "",
                "entrance_fee": str(row["입장(이용료)가격 정보"]) if row["입장(이용료)가격 정보"] else "",
                "tel": str(row["전화번호"]) if row["전화번호"] else "",
                "homepage": str(row["홈페이지"]) if row["홈페이지"] else "",
                "conditions": conditions if conditions not in ["해당없음", "제한사항 없음", ""] else "",
                "size_limit": size if size not in ["해당없음", "모두 가능", ""] else "모두 가능",
                "indoor": str(row["장소(실내) 여부"]),
                "outdoor": str(row["장소(실외)여부"]),
                "extra_fee": extra_fee if extra_fee not in ["없음", "해당없음", ""] else "없음",
                "source": "전국반려동물동반가능문화시설",
            })

        collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids,
        )

        print(f"  진행: {min(i + BATCH_SIZE, total)}/{total}")

    print(f"\n✅ 적재 완료! 총 {collection.count()}개 저장됨")


def main():
    df = load_and_filter(CSV_PATH)
    embed_and_store(df)


if __name__ == "__main__":
    main()
