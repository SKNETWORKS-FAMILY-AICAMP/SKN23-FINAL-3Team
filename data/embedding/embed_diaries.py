import os
import chromadb

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

# ── 설정 ──────────────────────────────────────────────────────
CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../chroma_db")
COLLECTION_NAME = "dog_diaries"
MODEL_NAME = "jhgan/ko-sroberta-multitask"


def get_or_create_collection(client: chromadb.PersistentClient):
    """dog_diaries 컬렉션 가져오기 또는 생성"""
    try:
        collection = client.get_collection(COLLECTION_NAME)
        print(f"기존 '{COLLECTION_NAME}' 컬렉션 연결 (현재 {collection.count()}개)")
    except:
        collection = client.create_collection(
            COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"'{COLLECTION_NAME}' 컬렉션 새로 생성")
    return collection


def embed_diary(
    diary_id: str,
    user_id: str,
    pet_id: str,
    diary_text: str,
    diary_date: str,
    location: str = "",
    summary: str = "",
):
    """
    일기 생성 시 호출 — 일기 한 건을 벡터화해서 dog_diaries에 저장

    Parameters:
        diary_id: 일기 고유 ID (예: diary_20260410_user001)
        user_id: 사용자 ID
        pet_id: 강아지 ID
        diary_text: 일기 원문 텍스트
        diary_date: 일기 날짜 (YYYY-MM-DD)
        location: 장소 (선택)
        summary: 짧은 요약 키워드 (선택)
    """
    print(f"일기 임베딩 중: {diary_id}")

    # 모델 로드
    model = SentenceTransformer(MODEL_NAME)

    # ChromaDB 연결
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = get_or_create_collection(client)

    # 임베딩 생성
    embedding = model.encode(diary_text).tolist()

    # ChromaDB 저장
    collection.add(
        documents=[diary_text],
        embeddings=[embedding],
        metadatas=[{
            "user_id": user_id,
            "pet_id": pet_id,
            "diary_date": diary_date,
            "location": location,
            "summary": summary,
        }],
        ids=[diary_id],
    )

    print(f"✅ 일기 임베딩 완료: {diary_id}")


def search_similar_diaries(
    user_id: str,
    query_text: str,
    n_results: int = 3,
) -> list:
    """
    유사한 과거 일기 검색 — 일기 생성 시 RAG 컨텍스트용

    Parameters:
        user_id: 사용자 ID (본인 일기만 검색)
        query_text: 오늘 활동 텍스트
        n_results: 반환할 일기 수 (기본 3개)

    Returns:
        유사한 과거 일기 목록
    """
    model = SentenceTransformer(MODEL_NAME)
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = get_or_create_collection(client)

    if collection.count() == 0:
        print("저장된 일기가 없습니다.")
        return []

    embedding = model.encode(query_text).tolist()

    result = collection.query(
        query_embeddings=[embedding],
        n_results=n_results,
        where={"user_id": user_id},  # 해당 사용자 일기만 검색 (필수)
        include=["documents", "metadatas", "distances"]
    )

    diaries = []
    for i in range(len(result["ids"][0])):
        diaries.append({
            "id": result["ids"][0][i],
            "document": result["documents"][0][i],
            "metadata": result["metadatas"][0][i],
            "similarity": 1 - result["distances"][0][i],
        })

    return diaries


def delete_diary(diary_id: str):
    """일기 삭제 — 일기 삭제 시 Vector DB에서도 제거"""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = get_or_create_collection(client)
    collection.delete(ids=[diary_id])
    print(f"✅ 일기 삭제 완료: {diary_id}")


# ── 테스트용 ──────────────────────────────────────────────────
if __name__ == "__main__":
    # 테스트용 일기 추가
    embed_diary(
        diary_id="diary_20260410_user001",
        user_id="user_001",
        pet_id="pet_001",
        diary_text="오늘 한강에서 신나게 뛰어놀았다. 바람도 시원하고 냄새가 너무 좋았어!",
        diary_date="2026-04-10",
        location="한강공원",
        summary="한강공원 산책",
    )

    # 유사 일기 검색 테스트
    results = search_similar_diaries(
        user_id="user_001",
        query_text="강가에서 산책했어요",
    )

    print("\n=== 유사 일기 검색 결과 ===")
    for r in results:
        print(f"  [{r['id']}] 유사도: {r['similarity']:.4f}")
        print(f"  내용: {r['document'][:50]}...")