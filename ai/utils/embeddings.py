# ai/utils/embeddings.py

from sentence_transformers import SentenceTransformer

MODEL_NAME = "jhgan/ko-sroberta-multitask"

_model = None

def get_embedding_model() -> SentenceTransformer:
    """
        임베딩 모델 싱글톤 반환
        → 처음 한 번만 로드, 이후엔 같은 모델 재사용 (메모리 낭비를 피하기 위해서)
    """
    global _model
    if _model is None:
        print(f"임베딩 모델 로드 중: {MODEL_NAME}")
        _model = SentenceTransformer(MODEL_NAME)
        print("모델 로드 완료!")
    return _model

def embed_text(text: str) -> list:
    """텍스트 한 건 임베딩"""
    model = get_embedding_model()
    return model.encode(text).tolist()

def embed_texts(texts: list) -> list:
    """텍스트 여러 건 임베딩"""
    model = get_embedding_model()
    return model.encode(texts).tolist()