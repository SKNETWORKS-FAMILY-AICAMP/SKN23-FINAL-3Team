# -*- coding: utf-8 -*-
"""
ai/diary_server.py
------------------
DB/SSH 없이 AI 일기·이미지 생성 엔드포인트만 띄우는 경량 테스트 서버.

실행:
    # 프로젝트 루트에서
    uvicorn ai.diary_server:app --port 8001 --reload

    # 또는 ai/ 디렉토리에서
    uvicorn diary_server:app --port 8001 --reload

※ 포트 정책
    - 8000: 메인 백엔드 (back/main.py) — DB/SSH 포함
    - 8001: AI 테스트 서버 (ai/diary_server.py) — DB/SSH 없음
"""

import json
import os
import sys

# 프로젝트 루트를 path에 추가
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

# .env 로드 (OPENAI_API_KEY 등)
from dotenv import load_dotenv
load_dotenv(os.path.join(_root, ".env"))

from back.api.core.config import settings

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel

from ai.prompts.diary_prompt_builder import DiaryPromptBuilder

_diary_prompt_builder = DiaryPromptBuilder()
from ai.eval.evaluator import create_diary_session, complete_image_eval, print_eval_summary

app = FastAPI(title="AI Diary Test Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_client: AsyncOpenAI | None = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


class DiaryRequest(BaseModel):
    pet_id: str = "default"
    pet_name: str
    breed: str = "강아지"
    breed_en: str | None = None
    birth_date: str | None = None
    personalities: list[str] = []
    owner_name: str = ""
    main_answers: list[str]
    additional_answers: list[str] = []
    diary_type: str
    emotion_emoji: str


class DiaryResponse(BaseModel):
    title: str
    content: str
    summary: str
    image_prompt_base: str
    image_prompt: str
    session_id: str


class ImageRequest(BaseModel):
    image_prompt: str
    session_id: str = ""


class ImageResponse(BaseModel):
    image_base64: str


@app.get("/health")
async def health():
    return {"status": "ok", "server": "ai-diary-test"}


@app.post("/api/diary/generate", response_model=DiaryResponse)
async def generate_diary(req: DiaryRequest) -> DiaryResponse:
    all_answers = req.main_answers + req.additional_answers
    conversation_summary = "\n".join(f"보호자: {a}" for a in all_answers if a.strip())
    if not conversation_summary:
        raise HTTPException(status_code=400, detail="답변 내용이 없습니다.")

    prompt = _diary_prompt_builder.build_diary_prompt(
        pet_name=req.pet_name,
        breed=req.breed,
        birth_date=req.birth_date,
        personalities=req.personalities,
        owner_name=req.owner_name,
        diary_type=req.diary_type,
        emotion=req.emotion_emoji,
        conversation_summary=conversation_summary,
    )

    response = await get_client().chat.completions.create(
        model=settings.GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,   # 낮출수록 일관성↑ 창의성↓ (0.7→0.4)
        top_p=0.9,         # P값: 확률 상위 90% 토큰만 선택
        seed=42,           # 시드값: 동일 입력 시 재현 가능한 결과
        frequency_penalty=0.1,  # 반복 표현 억제
    )

    raw = response.choices[0].message.content or ""
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM 응답 파싱 실패: {raw[:200]}")

    image_prompt = _diary_prompt_builder.build_final_image_prompt(
        image_prompt_base=data.get("image_prompt_base", ""),
        breed=req.breed,
        breed_en=req.breed_en,
        birth_date=req.birth_date,
        personalities=req.personalities,
        all_answers=all_answers,
        emotion=req.emotion_emoji,
    )

    session_id = create_diary_session(
        diary_llm_prompt=prompt,
        image_prompt_base=data.get("image_prompt_base", ""),
        image_prompt_final=image_prompt,
        diary_title=data.get("title", ""),
        diary_content=data.get("content", ""),
        diary_summary=data.get("summary", ""),
        pet_name=req.pet_name,
        breed=req.breed,
        breed_en=req.breed_en or "",
        emotion=req.emotion_emoji,
        diary_type=req.diary_type,
        personalities=req.personalities,
    )

    return DiaryResponse(
        title=data.get("title", "오늘의 일기"),
        content=data.get("content", ""),
        summary=data.get("summary", ""),
        image_prompt_base=data.get("image_prompt_base", ""),
        image_prompt=image_prompt,
        session_id=session_id,
    )


@app.post("/api/diary/generate-image", response_model=ImageResponse)
async def generate_image(req: ImageRequest) -> ImageResponse:
    if not req.image_prompt.strip():
        raise HTTPException(status_code=400, detail="image_prompt가 비어 있습니다.")

    response = await get_client().images.generate(
        model=settings.GPT_IMAGE_MODEL,
        prompt=req.image_prompt,
        size="1024x1024",
        quality="medium",  # 옵션값: low→medium (얼굴·디테일 품질 향상)
        n=1,
    )
    b64 = response.data[0].b64_json
    if not b64:
        raise HTTPException(status_code=500, detail="이미지 생성 실패")

    import asyncio
    loop = asyncio.get_event_loop()
    eval_record = await loop.run_in_executor(
        None,
        lambda: complete_image_eval(
            session_id=req.session_id,
            image_b64=b64,
            image_prompt_final=req.image_prompt,
        ),
    )
    print_eval_summary(eval_record)

    return ImageResponse(image_base64=b64)
