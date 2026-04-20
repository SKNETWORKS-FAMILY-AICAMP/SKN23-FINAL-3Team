# -*- coding: utf-8 -*-
from sentence_transformers import SentenceTransformer
from ai.core.interfaces.base_embedder import BaseEmbedder

MODEL_NAME = "jhgan/ko-sroberta-multitask"


class SentenceEmbedder(BaseEmbedder):

    def __init__(self, model_name: str = MODEL_NAME):
        print(f"임베딩 모델 로드 중: {model_name}")
        self._model = SentenceTransformer(model_name)
        print("모델 로드 완료!")

    def embed(self, text: str) -> list[float]:
        """텍스트 한 건 임베딩"""
        return self._model.encode(text).tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """텍스트 여러 건 임베딩"""
        return self._model.encode(texts).tolist()