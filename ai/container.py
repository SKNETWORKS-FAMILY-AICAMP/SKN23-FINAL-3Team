# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv
from openai import AsyncOpenAI

from ai.infrastructure.embedder import SentenceEmbedder
from ai.infrastructure.vector_store import ChromaVectorStore
from ai.infrastructure.cost_tracker import OpenAICostTracker

from ai.retrievers.places_retriever import PlacesRetriever
from ai.retrievers.breed_retriever import BreedRetriever
from ai.retrievers.diary_retriever import DiaryRetriever
from ai.retrievers.query_parser import QueryParser

from ai.scorers.dog_scorer import DogScorer
from ai.scorers.owner_scorer import OwnerScorer

from ai.prompts.diary_prompt_builder import DiaryPromptBuilder
from ai.prompts.places_prompt_builder import PlacesPromptBuilder

from ai.chains.places_chain import PlacesChain
from ai.chains.diary_chain import DiaryChain

load_dotenv()

DEFAULT_CHROMA_PATH = os.path.join(os.path.dirname(__file__), "../data/chroma_db")


class AIContainer:

    def __init__(
        self,
        openai_api_key: str | None = None,
        chroma_path: str = DEFAULT_CHROMA_PATH,
    ):
        # API 키 — 인자로 받거나 환경변수에서 읽기
        api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        # ── 1. 기본 도구 생성 ──────────────────────────────
        self._embedder     = SentenceEmbedder()
        self._vector_store = ChromaVectorStore(path=chroma_path)
        self._cost_tracker = OpenAICostTracker()
        self._llm          = AsyncOpenAI(api_key=api_key)

        # ── 2. Retrievers ──────────────────────────────────
        self._breed_retriever  = BreedRetriever(self._vector_store, self._embedder)
        self._diary_retriever  = DiaryRetriever(self._vector_store, self._embedder)
        self._places_retriever = PlacesRetriever(self._vector_store, self._embedder)
        self._query_parser     = QueryParser(llm_client=self._llm)

        # ── 3. Scorers ─────────────────────────────────────
        self._dog_scorer   = DogScorer()
        self._owner_scorer = OwnerScorer()

        # ── 4. Prompt Builders ─────────────────────────────
        self._diary_prompt  = DiaryPromptBuilder()
        self._places_prompt = PlacesPromptBuilder()

        # ── 5. 최종 파이프라인 조립 ────────────────────────
        self.places_chain = PlacesChain(
            retriever      = self._places_retriever,
            dog_scorer     = self._dog_scorer,
            owner_scorer   = self._owner_scorer,
            prompt_builder = self._places_prompt,
            llm_client     = self._llm,
            cost_tracker   = self._cost_tracker,
        )

        self.diary_chain = DiaryChain(
            breed_retriever = self._breed_retriever,
            diary_retriever = self._diary_retriever,
            prompt_builder  = self._diary_prompt,
            llm_client      = self._llm,
            cost_tracker    = self._cost_tracker,
        )