# -*- coding: utf-8 -*-
import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

DEFAULT_CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../../data/chroma_db")

# 컬렉션 이름 상수 (기존 코드에서 그대로 가져옴)
COLLECTION_BREEDS  = "dog_breeds"
COLLECTION_DIARIES = "dog_diaries"
COLLECTION_PLACES  = "dog_places"


class ChromaVectorStore:

    def __init__(self, path: str = DEFAULT_CHROMA_PATH):
        self._client = chromadb.PersistentClient(path=path)

    def get_collection(self, collection_name: str):
        """컬렉션 반환"""
        return self._client.get_collection(collection_name)

    def query(
        self,
        collection_name: str,
        embedding: list[float],
        n_results: int = 5,
        where: dict | None = None,
    ) -> dict:
        """컬렉션에서 유사 벡터 검색"""
        collection = self.get_collection(collection_name)
        kwargs = {
            "query_embeddings": [embedding],
            "n_results": n_results,
        }
        if where:
            kwargs["where"] = where
        return collection.query(**kwargs)