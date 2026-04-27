# -*- coding: utf-8 -*-
import json
from openai import AsyncOpenAI

from ai.core.interfaces.base_chain import BaseChain
from ai.core.interfaces.base_prompt_builder import BasePromptBuilder
from ai.retrievers.breed_retriever import BreedRetriever
from ai.retrievers.diary_retriever import DiaryRetriever
from ai.infrastructure.cost_tracker import OpenAICostTracker

MODEL = "gpt-4.1-mini"
IMAGE_MODEL = "gpt-image-1"


class DiaryChain(BaseChain):

    def __init__(
        self,
        breed_retriever: BreedRetriever,
        diary_retriever: DiaryRetriever,
        prompt_builder: BasePromptBuilder,
        llm_client: AsyncOpenAI,
        cost_tracker: OpenAICostTracker,
    ):
        self._breed_retriever  = breed_retriever
        self._diary_retriever  = diary_retriever
        self._prompt_builder   = prompt_builder
        self._llm              = llm_client
        self._cost_tracker     = cost_tracker

    async def run(
        self,
        pet_name: str,
        breed: str,
        breed_en: str | None,
        birth_date: str | None,
        personalities: list[str],
        diary_type: str,
        emotion: str,
        conversation_summary: str,
        user_id: str,
        owner_name: str = "",
    ) -> dict:
        """
        일기 생성 전체 파이프라인 실행

        Returns:
            {
                "title": "오늘도 신났다 멍!",
                "content": "일기 본문...",
                "summary": "한줄요약",
                "image_prompt_base": "A cute storybook dog...",
                "image_prompt_final": "완성된 이미지 프롬프트",
                "diary_llm_prompt": "GPT에 보낸 프롬프트 (평가용)",
                "breed_context": {...},
                "has_past_diaries": True,
            }
        """
        # Step 1. 견종 컨텍스트 검색
        breed_context = self._breed_retriever.get_breed_context(breed)

        # Step 2. 유사 과거 일기 검색
        past_diaries = self._diary_retriever.search(
            query=conversation_summary,
            user_id=user_id,
            n_results=3,
        )
        past_diaries_text = self._diary_retriever.format_context(past_diaries)

        # Step 3. 일기 프롬프트 구성
        diary_llm_prompt = self._prompt_builder.build_user_prompt(
            pet_name=pet_name,
            breed=breed,
            birth_date=birth_date,
            personalities=personalities,
            diary_type=diary_type,
            emotion=emotion,
            conversation_summary=conversation_summary,
            owner_name=owner_name,
        )

        # Step 4. GPT 호출 — 일기 생성
        print("GPT 일기 생성 중...")
        try:
            response = await self._llm.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": self._prompt_builder.build_system_prompt()},
                    {"role": "user",   "content": diary_llm_prompt},
                ],
                max_tokens=1500,
                temperature=0.85,
            )
            raw = response.choices[0].message.content.strip()
            await self._cost_tracker.track_chat(response, note="diary_chain")

        except Exception as e:
            print(f"GPT 일기 생성 오류: {e}")
            return {
                "title": "",
                "content": "",
                "summary": "",
                "image_prompt_base": "",
                "image_prompt_final": "",
                "diary_llm_prompt": diary_llm_prompt,
                "breed_context": breed_context,
                "has_past_diaries": len(past_diaries) > 0,
            }

        # Step 5. JSON 파싱
        try:
            clean  = raw.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean)
        except Exception as e:
            print(f"JSON 파싱 오류: {e}")
            return {
                "title": "",
                "content": raw,
                "summary": "",
                "image_prompt_base": "",
                "image_prompt_final": "",
                "diary_llm_prompt": diary_llm_prompt,
                "breed_context": breed_context,
                "has_past_diaries": len(past_diaries) > 0,
            }

        # Step 6. 이미지 프롬프트 완성
        image_prompt_base  = result.get("image_prompt_base", "")
        image_prompt_final = self._prompt_builder.build_final_image_prompt(
            image_prompt_base=image_prompt_base,
            breed=breed,
            breed_en=breed_en,
            birth_date=birth_date,
            personalities=personalities,
            all_answers=[conversation_summary],
            emotion=emotion,
        )

        return {
            "title":              result.get("title", ""),
            "content":            result.get("content", ""),
            "summary":            result.get("summary", ""),
            "image_prompt_base":  image_prompt_base,
            "image_prompt_final": image_prompt_final,
            "diary_llm_prompt":   diary_llm_prompt,
            "breed_context":      breed_context,
            "has_past_diaries":   len(past_diaries) > 0,
        }

    async def generate_image(
        self,
        image_prompt_final: str,
        quality: str = "low",
    ) -> str | None:
        """
        이미지 생성 (base64 반환)

        Parameters:
            image_prompt_final: build_final_image_prompt() 결과
            quality: "low" | "medium" | "high"

        Returns:
            base64 인코딩된 이미지 문자열, 실패 시 None
        """
        print("이미지 생성 중...")
        try:
            response = await self._llm.images.generate(
                model=IMAGE_MODEL,
                prompt=image_prompt_final,
                size="1024x1024",
                quality=quality,
                response_format="b64_json",
                n=1,
            )
            await self._cost_tracker.track_image(quality=quality, note="diary_chain")
            return response.data[0].b64_json

        except Exception as e:
            print(f"이미지 생성 오류: {e}")
            return None