# ai/llm/rag/breed_retriever.py
# 견종 성격 컨텍스트 검색 (dog_breeds)

from ai.utils.chroma_client import get_collection, COLLECTION_BREEDS
from ai.utils.embeddings import embed_text


def search_breed_context(breed_name: str) -> dict | None:
    """
    견종명으로 성격 컨텍스트 검색
    → 일기 생성 프롬프트에 주입할 견종 성격 정보 반환

    Parameters:
        breed_name: 영문 견종명 (소문자, 예: "pomeranian")

    Returns:
        {
            "breed_name": "pomeranian",
            "breed_name_ko": "포메라니안",
            "activity_level": "medium",
            "temperament": "활발한, 호기심 많은, ...",
            "document": "포메라니안은 활발하고 호기심이 많으며..."
        }
        검색 결과 없으면 None 반환
    """
    try:
        collection = get_collection(COLLECTION_BREEDS)

        # breed_name metadata filtering → Top-1
        result = collection.query(
            query_embeddings=[embed_text(breed_name)],
            n_results=1,
            where={"breed_name": breed_name.lower().strip()},
            include=["documents", "metadatas", "distances"]
        )

        if not result["ids"][0]:
            print(f"견종 '{breed_name}' 검색 결과 없음")
            return None

        metadata = result["metadatas"][0][0]
        document = result["documents"][0][0]

        return {
            "breed_name": metadata.get("breed_name", ""),
            "breed_name_ko": metadata.get("breed_name_ko", ""),
            "activity_level": metadata.get("activity_level", "medium"),
            "temperament": metadata.get("temperament", ""),
            "document": document,
        }

    except Exception as e:
        print(f"breed_retriever 오류: {e}")
        return None


def get_default_breed_context() -> dict:
    """
    견종 정보 없을 때 기본값 반환
    → 오류 처리용
    """
    return {
        "breed_name": "unknown",
        "breed_name_ko": "알 수 없음",
        "activity_level": "medium",
        "temperament": "활발하고 친근한 성격",
        "document": "이 강아지는 활발하고 친근한 성격을 가지고 있어요.",
    }


def get_breed_context(breed_name: str) -> dict:
    """
    견종 성격 컨텍스트 반환 (검색 실패 시 기본값 반환)
    → 외부에서 주로 이 함수를 호출

    Parameters:
        breed_name: 영문 견종명 (소문자)

    Returns:
        견종 성격 컨텍스트 dict
    """
    result = search_breed_context(breed_name)
    if result is None:
        print(f"기본 견종 컨텍스트 사용")
        return get_default_breed_context()
    return result