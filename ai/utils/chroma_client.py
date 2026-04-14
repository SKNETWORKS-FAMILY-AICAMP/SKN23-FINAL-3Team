# ai/utils/chroma_client.py

import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../../data/chroma_db")

_client = None

def get_chroma_client() -> chromadb.PersistentClient:
    """
        ChromaDB 클라이언트 싱글톤 반환
        → ChromaDB 연결(접속) 을 한 번만
    """
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client

def get_collection(collection_name: str):
    """컬렉션 반환"""
    client = get_chroma_client()
    return client.get_collection(collection_name)

# 컬렉션 이름 상수
COLLECTION_BREEDS = "dog_breeds"
COLLECTION_DIARIES = "dog_diaries"
COLLECTION_PLACES = "dog_places"