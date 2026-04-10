import os
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# ── 설정 ──────────────────────────────────────────────────────
CSV_PATH = os.path.join(os.path.dirname(__file__), "../data/경기도_반려동물_동반_관광정보_위경도추가.csv")
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../chroma_db")
COLLECTION_NAME = "dog_places"
MODEL_NAME = "jhgan/ko-sroberta-multitask"


def map_category(name: str) -> str:
    """업체명 기준 카테고리 분류"""
    if "놀이터" in name:
        return "놀이터"
    elif "공원" in name:
        return "공원"
    elif "휴양림" in name:
        return "관광지"
    elif "랜드" in name or "파크" in name:
        return "관광지"
    else:
        return "관광지"


def load_and_filter(csv_path: str) -> pd.DataFrame:
    """CSV 로드 및 전처리"""
    print("CSV 로드 중...")
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    print(f"원본 데이터: {len(df)}개")

    # 앞뒤 공백, 개행문자 제거
    df["업체명"] = df["업체명"].str.strip().str.replace("\n", " ")
    df["주소"] = df["주소"].str.strip().str.replace("\n", " ")

    # 위경도 소수점 4자리 통일
    df["위도"] = df["위도"].round(4)
    df["경도"] = df["경도"].round(4)

    # city 필드 — 지역명에서 추출
    df["city"] = "경기도"

    # category 매핑
    df["category"] = df["업체명"].apply(map_category)

    # 운영시간 null → 빈 문자열
    df["이용시간"] = df["이용시간"].fillna("").str.strip()

    return df


def build_document(row) -> str:
    """벡터화할 document 문장 구성"""
    name = row["업체명"]
    city = row["city"]
    category = row["category"]

    doc = f"{name}은 {city}에 위치한 {category} 장소로 반려견 동반이 가능하다."

    return doc


def embed_and_store(df: pd.DataFrame):
    """임베딩 생성 및 ChromaDB 기존 컬렉션에 추가 저장"""

    # 모델 로드
    print(f"\n임베딩 모델 로드 중: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("모델 로드 완료!")

    # ChromaDB 초기화 — 기존 컬렉션 가져오기 (삭제 안 함)
    print(f"\nChromaDB 초기화: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 연결 (현재 {collection.count()}개)")
    except:
        collection = client.create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"'{COLLECTION_NAME}' 컬렉션 새로 생성")

    # 적재 시작 ID offset (기존 데이터와 충돌 방지)
    offset = collection.count()

    total = len(df)
    print(f"\n총 {total}개 데이터 적재 시작 (ID offset: {offset})...")

    documents = [build_document(row) for _, row in df.iterrows()]
    ids = [f"place_gyeonggi_{offset + j}" for j in range(total)]

    # 임베딩 생성
    embeddings = model.encode(documents, show_progress_bar=True).tolist()

    # metadata 구성
    metadatas = []
    for _, row in df.iterrows():
        metadatas.append({
            "name": str(row["업체명"]),
            "address": str(row["주소"]),
            "category": str(row["category"]),
            "city": str(row["city"]),
            "lat": float(row["위도"]),
            "lng": float(row["경도"]),
            "open_hours": str(row["이용시간"]) if row["이용시간"] else "운영 시간 미제공 · 방문 전 문의 권장",
            "conditions": "",
            "size_limit": "모두 가능",
            "indoor": "N",
            "outdoor": "Y",
            "extra_fee": "없음",
            "source": "경기관광공사",
        })

    collection.add(
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids,
    )

    print(f"\n✅ 적재 완료! 총 {collection.count()}개 저장됨")


def main():
    df = load_and_filter(CSV_PATH)
    embed_and_store(df)


if __name__ == "__main__":
    main()