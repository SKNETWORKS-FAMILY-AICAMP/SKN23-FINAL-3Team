# -*- coding: utf-8 -*-
from ai.core.interfaces.base_retriever import BaseRetriever
from ai.core.interfaces.base_embedder import BaseEmbedder
from ai.infrastructure.vector_store import ChromaVectorStore, COLLECTION_DIARIES


class DiaryRetriever(BaseRetriever):

    def __init__(self, vector_store: ChromaVectorStore, embedder: BaseEmbedder):
        self._store    = vector_store
        self._embedder = embedder

    def search(
        self,
        query: str,
        user_id: str = None,
        n_results: int = 3,
        **kwargs,
    ) -> list[dict]:
        try:
            collection = self._store.get_collection(COLLECTION_DIARIES)

            if collection.count() == 0:
                print("저장된 일기가 없습니다.")
                return []

            embedding = self._embedder.embed(query)

            result = self._store.query(
                collection_name=COLLECTION_DIARIES,
                embedding=embedding,
                n_results=n_results,
                where={"user_id": user_id} if user_id else None,
            )

            if not result["ids"][0]:
                print(f"user_id '{user_id}'의 유사 일기 없음")
                return []

            diaries = []
            for i in range(len(result["ids"][0])):
                metadata = result["metadatas"][0][i]
                diaries.append({
                    "id":         result["ids"][0][i],
                    "document":   result["documents"][0][i],
                    "diary_date": metadata.get("diary_date", ""),
                    "location":   metadata.get("location", ""),
                    "summary":    metadata.get("summary", ""),
                    "similarity": round(1 - result["distances"][0][i], 4),
                })

            return diaries

        except Exception as e:
            print(f"diary_retriever 오류: {e}")
            return []

    def format_context(self, results: list[dict]) -> str:
        if not results:
            return ""

        formatted = []
        for diary in results:
            date     = diary.get("diary_date", "")
            location = diary.get("location", "")
            document = diary.get("document", "")

            header = f"[{date} / {location}]" if location else f"[{date}]"
            formatted.append(f"{header}\n{document}")

        return "\n\n".join(formatted)