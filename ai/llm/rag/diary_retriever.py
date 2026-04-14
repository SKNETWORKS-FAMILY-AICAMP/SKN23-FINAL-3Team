# ai/llm/rag/diary_retriever.py
# 유사 과거 일기 검색 (dog_diaries)

from ai.utils.chroma_client import get_collection, COLLECTION_DIARIES
from ai.utils.embeddings import embed_text


def search_similar_diaries(
    user_id: str,
    query_text: str,
    n_results: int = 3,
) -> list:
    """
    유사한 과거 일기 검색
    → 개인화 일기 생성 시 RAG 컨텍스트용

    Parameters:
        user_id: 사용자 ID (본인 일기만 검색, 필수)
        query_text: 오늘 활동 텍스트 (예: "한강에서 산책했어요")
        n_results: 반환할 일기 수 (기본 3개)

    Returns:
        [
            {
                "id": "diary_20260410_user001",
                "document": "오늘 한강에서 신나게 뛰어놀았다...",
                "diary_date": "2026-04-10",
                "location": "한강공원",
                "summary": "한강공원 산책",
                "similarity": 0.85
            },
            ...
        ]
        검색 결과 없으면 빈 리스트 반환
    """
    try:
        collection = get_collection(COLLECTION_DIARIES)

        if collection.count() == 0:
            print("저장된 일기가 없습니다.")
            return []

        result = collection.query(
            query_embeddings=[embed_text(query_text)],
            n_results=n_results,
            where={"user_id": user_id},  # 본인 일기만 검색 (필수)
            include=["documents", "metadatas", "distances"]
        )

        if not result["ids"][0]:
            print(f"user_id '{user_id}'의 유사 일기 없음")
            return []

        diaries = []
        for i in range(len(result["ids"][0])):
            metadata = result["metadatas"][0][i]
            diaries.append({
                "id": result["ids"][0][i],
                "document": result["documents"][0][i],
                "diary_date": metadata.get("diary_date", ""),
                "location": metadata.get("location", ""),
                "summary": metadata.get("summary", ""),
                "similarity": round(1 - result["distances"][0][i], 4),
            })

        return diaries

    except Exception as e:
        print(f"diary_retriever 오류: {e}")
        return []


def format_past_diaries(diaries: list) -> str:
    """
    과거 일기 목록 → 프롬프트에 넣을 텍스트로 변환

    Parameters:
        diaries: search_similar_diaries() 반환값

    Returns:
        "[2026-04-10 / 한강공원]\n오늘 한강에서 신나게..."
    """
    if not diaries:
        return ""

    formatted = []
    for diary in diaries:
        date = diary.get("diary_date", "")
        location = diary.get("location", "")
        document = diary.get("document", "")

        header = f"[{date} / {location}]" if location else f"[{date}]"
        formatted.append(f"{header}\n{document}")

    return "\n\n".join(formatted)