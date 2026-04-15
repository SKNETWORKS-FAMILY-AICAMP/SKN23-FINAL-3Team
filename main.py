import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))  # 프로젝트 루트

from contextlib import asynccontextmanager
from openai import AsyncOpenAI
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from ai.llm.prompts.diary_prompt import build_diary_prompt, build_final_image_prompt
from ai.eval.evaluator import create_diary_session, complete_image_eval, print_eval_summary

load_dotenv()

_client: AsyncOpenAI | None = None

def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="멍일기 API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── 요청/응답 스키마 ──────────────────────────────────────
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
    session_id: str  # 평가 추적용 — generate-image 호출 시 함께 전달


class ImageRequest(BaseModel):
    image_prompt: str
    session_id: str = ""  # DiaryResponse에서 받은 값 전달 (없으면 단독 평가)


class ImageResponse(BaseModel):
    image_base64: str


# ── 일기 생성 ─────────────────────────────────────────────
@app.post("/api/diary/generate", response_model=DiaryResponse)
async def generate_diary(req: DiaryRequest) -> DiaryResponse:
    all_answers = req.main_answers + req.additional_answers
    conversation_summary = "\n".join(
        f"보호자: {a}" for a in all_answers if a.strip()
    )
    if not conversation_summary:
        raise HTTPException(status_code=400, detail="답변 내용이 없습니다.")

    prompt = build_diary_prompt(
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
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    raw = response.choices[0].message.content or ""
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM 응답 파싱 실패: {raw[:200]}")

    image_prompt = build_final_image_prompt(
        image_prompt_base=data.get("image_prompt_base", ""),
        breed=req.breed,
        breed_en=req.breed_en,
        birth_date=req.birth_date,
        personalities=req.personalities,
        all_answers=all_answers,
        emotion=req.emotion_emoji,
    )

    # ── 평가 세션 생성 (두 프롬프트 저장) ───────────────────────────
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


# ── 이미지 생성 ───────────────────────────────────────────
@app.post("/api/diary/generate-image", response_model=ImageResponse)
async def generate_image(req: ImageRequest) -> ImageResponse:
    if not req.image_prompt.strip():
        raise HTTPException(status_code=400, detail="image_prompt가 비어 있습니다.")

    response = await get_client().images.generate(
        model="gpt-image-1",
        prompt=req.image_prompt,
        size="1024x1024",
        quality="low",
        n=1,
    )
    b64 = response.data[0].b64_json
    if not b64:
        raise HTTPException(status_code=500, detail="이미지 생성 실패")

    # ── 평가 실행 + 저장 (비동기 블로킹 없이 별도 처리) ──────────────
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


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
