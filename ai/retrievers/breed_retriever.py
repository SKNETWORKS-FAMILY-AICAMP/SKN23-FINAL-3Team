# -*- coding: utf-8 -*-
from ai.core.interfaces.base_retriever import BaseRetriever
from ai.core.interfaces.base_embedder import BaseEmbedder
from ai.infrastructure.vector_store import ChromaVectorStore, COLLECTION_BREEDS


class BreedRetriever(BaseRetriever):

    def __init__(self, vector_store: ChromaVectorStore, embedder: BaseEmbedder):
        self._store    = vector_store
        self._embedder = embedder

    def search(self, query: str, **kwargs) -> list[dict]:
        try:
            embedding = self._embedder.embed(query)

            result = self._store.query(
                collection_name=COLLECTION_BREEDS,
                embedding=embedding,
                n_results=1,
                where={"breed_name": query.lower().strip()},
            )

            if not result["ids"][0]:
                print(f"견종 '{query}' 검색 결과 없음")
                return []

            metadata = result["metadatas"][0][0]
            document = result["documents"][0][0]

            return [{
                "breed_name":    metadata.get("breed_name", ""),
                "breed_name_ko": metadata.get("breed_name_ko", ""),
                "activity_level": metadata.get("activity_level", "medium"),
                "temperament":   metadata.get("temperament", ""),
                "document":      document,
            }]

        except Exception as e:
            print(f"breed_retriever 오류: {e}")
            return []

    def format_context(self, results: list[dict]) -> str:
        if not results:
            return ""
        breed = results[0]
        return breed.get("document", "")

    def get_breed_context(self, breed_name: str) -> dict:
        """견종 성격 컨텍스트 반환 (검색 실패 시 기본값 반환)"""
        results = self.search(breed_name)
        if not results:
            print("기본 견종 컨텍스트 사용")
            return self._get_default_context()
        return results[0]

    def _get_default_context(self) -> dict:
        return {
            "breed_name":    "unknown",
            "breed_name_ko": "알 수 없음",
            "activity_level": "medium",
            "temperament":   "활발하고 친근한 성격",
            "document":      "이 강아지는 활발하고 친근한 성격을 가지고 있어요.",
        }