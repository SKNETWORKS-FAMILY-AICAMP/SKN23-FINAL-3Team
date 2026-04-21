# -*- coding: utf-8 -*-
"""
main.py
-------
FastAPI 애플리케이션 진입점.

[역할]
- lifespan: 앱 시작 시 SSH 터널(local) + DB 엔진 초기화, 종료 시 정리
- 라우터 등록: 모든 도메인 라우터 포함
- APScheduler: 탈퇴 10일 후 Hard Delete 배치 등록
- CORS 설정
- 공통 예외 핸들러

실행 방법::

        # 개발 서버 (hot reload)
        uvicorn main:app --reload --host 0.0.0.0 --port 8000

        # 프로덕션
        uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
"""

from __future__ import annotations

import os
import json
import logging

from sqlalchemy import text
from openai import AsyncOpenAI
from pydantic import BaseModel
from core.config import settings
from typing import AsyncGenerator
from core.database import get_engine
from sshtunnel import SSHTunnelForwarder
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, status
from logging.handlers import RotatingFileHandler
from fastapi.middleware.cors import CORSMiddleware
from services.intent_service import warmup_intent_model
from core.database import close_db, init_db, init_engine
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.scheduler_service import hard_delete_withdrawn_users

# =============================================================================
# 로깅 설정
# back/api/main.py → <project_root>/logs/app.log
# - 콘솔(stderr)과 파일에 동시 기록
# - 10MB 단위로 회전, 최대 5개 백업 유지
# - 환경변수 LOG_DIR / LOG_LEVEL 로 오버라이드 가능
# =============================================================================

def _configure_logging() -> None:
    _default_log_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "logs")
    )
    log_dir = os.getenv("LOG_DIR", _default_log_dir)
    os.makedirs(log_dir, exist_ok=True)

    level = getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper(), logging.INFO)
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    root = logging.getLogger()
    root.setLevel(level)
    # uvicorn 기본 핸들러와 중복되지 않도록 기존 핸들러 제거 후 재설정
    root.handlers.clear()

    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(fmt))
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(logging.Formatter(fmt))
    root.addHandler(file_handler)

    # uvicorn 로거도 동일한 핸들러 사용
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True  # root 로거 핸들러 재사용


_configure_logging()

# # AI 일기/이미지 생성 모듈 (프로젝트 루트의 ai/ 패키지)
logger = logging.getLogger(__name__)

try:
    from ai.prompts.diary_prompt_builder import DiaryPromptBuilder
    from ai.eval.evaluator import create_diary_session, complete_image_eval, print_eval_summary
    _diary_prompt_builder = DiaryPromptBuilder()
    _AI_AVAILABLE = True
except ImportError:
    _AI_AVAILABLE = False
    _diary_prompt_builder = None
    logger.warning("[AI] ai 패키지 임포트 실패 — /api/diary/* 엔드포인트 비활성화")

# try:
#     from ai.llm.prompts.diary_prompt import build_diary_prompt, build_final_image_prompt
#     from ai.eval.evaluator import create_diary_session, complete_image_eval, print_eval_summary
#     _AI_AVAILABLE = True
# except ImportError:
#     _AI_AVAILABLE = False
#     logger.warning("[AI] ai 패키지 임포트 실패 — /api/diary/* 엔드포인트 비활성화")

# =============================================================================
# SSH 터널 관리 (local 환경 전용)
# =============================================================================

_ssh_tunnel = None


def _start_ssh_tunnel() -> tuple[str, int]:
    """
        local 환경에서 EC2 SSH 터널을 시작합니다.

        Returns:
                (host, port) - DB 연결에 사용할 로컬 바인딩 주소와 포트
    """
    global _ssh_tunnel

    _ssh_tunnel = SSHTunnelForwarder(
        (settings.SSH_HOST, settings.SSH_PORT),
        ssh_username=settings.SSH_USER,
        ssh_pkey=settings.SSH_PKEY,
        remote_bind_address=(settings.DB_HOST, settings.DB_PORT),
        local_bind_address=("127.0.0.1",),
    )
    _ssh_tunnel.start()
    host = "127.0.0.1"
    port = _ssh_tunnel.local_bind_port
    logger.info(f"[SSH Tunnel] EC2({settings.SSH_HOST}) -> RDS 터널 연결 완료: localhost:{port}")
    return host, port


def _stop_ssh_tunnel() -> None:
    """SSH 터널을 종료합니다."""
    global _ssh_tunnel
    if _ssh_tunnel and _ssh_tunnel.is_active:
        _ssh_tunnel.stop()
        logger.info("[SSH Tunnel] 연결 종료")


# =============================================================================
# APScheduler 배치 작업 등록
# =============================================================================

def _setup_scheduler(app: FastAPI) -> None:
    """APScheduler를 초기화하고 배치 작업을 등록합니다."""

    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    # 매일 새벽 3시: 탈퇴 10일 경과 사용자 Hard Delete
    scheduler.add_job(
        hard_delete_withdrawn_users,
        trigger="cron",
        hour=3,
        minute=0,
        id="hard_delete_users",
        replace_existing=True,
    )

    scheduler.start()
    app.state.scheduler = scheduler
    logger.info("[Scheduler] APScheduler 시작 완료")


# =============================================================================
# 앱 Lifespan (시작 / 종료 훅)
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
        앱 시작/종료 시 실행되는 lifespan 컨텍스트 매니저.

        시작:
            1. local 환경이면 SSH 터널 오픈
            2. DB 엔진 & 세션 팩토리 초기화
            3. APScheduler 배치 등록
        종료:
            1. 스케줄러 종료
            2. DB 커넥션 풀 해제
            3. SSH 터널 종료
    """
    # ── 시작 ────────────────────────────────────────────────────────────────
    logger.info(f"[App] 서버 환경: SERVER={settings.SERVER}")

    # local 환경이면 SSH 터널 먼저 오픈
    if settings.SERVER == "local":
        db_host, db_port = _start_ssh_tunnel()
    else:
        db_host, db_port = settings.DB_HOST, settings.DB_PORT

    # DB 엔진 초기화 (터널 포트 적용)
    init_engine(host=db_host, port=db_port)
    logger.info(f"[DB] AsyncEngine 초기화 완료: {db_host}:{db_port}/{settings.DB_NAME}")

    # 스케줄러 등록
    try:
        _setup_scheduler(app)
    except Exception as e:
        logger.warning(f"[Scheduler] 초기화 실패 (무시하고 계속): {e}")

    # 의도 분류 모델 워밍업 (첫 요청 지연 방지, 실패 시 lazy-load 로 폴백)
    try:
        warmup_intent_model()
    except Exception as e:
        logger.warning(f"[Intent] 워밍업 훅 등록 실패 (무시): {e}")

    # 커스텀 견종 (Dog API에 없는 믹스견) 초기 삽입
    try:
        from sqlalchemy import select
        from core.database import AsyncSessionLocal
        from models.breed import Breed, BreedSizeEnum

        _CUSTOM_BREEDS = [
            {"name_ko": "믹스견(소형)", "name_en": "Mixed Breed (Small)", "size": BreedSizeEnum.small},
            {"name_ko": "믹스견(중형)", "name_en": "Mixed Breed (Medium)", "size": BreedSizeEnum.medium},
            {"name_ko": "믹스견(대형)", "name_en": "Mixed Breed (Large)", "size": BreedSizeEnum.large},
        ]
        async with AsyncSessionLocal() as _sess:
            for _cb in _CUSTOM_BREEDS:
                _res = await _sess.execute(select(Breed).where(Breed.name_ko == _cb["name_ko"]))
                if _res.scalar_one_or_none() is None:
                    _sess.add(Breed(name_ko=_cb["name_ko"], name_en=_cb["name_en"], top10=False, size=_cb["size"]))
            await _sess.commit()
        logger.info("[DB] 커스텀 견종(믹스견 3종) 확인/삽입 완료")
    except Exception as e:
        logger.warning(f"[DB] 커스텀 견종 삽입 실패 (무시): {e}")

    # AIContainer 초기화 (ChromaDB + 임베딩 모델)
    try:
        from ai.container import AIContainer
        app.state.ai_container = AIContainer(
            openai_api_key=settings.OPENAI_API_KEY
        )
        logger.info("[AI] AIContainer 초기화 완료")
    except Exception as e:
        logger.warning(f"[AI] AIContainer 초기화 실패 (무시): {e}")
        app.state.ai_container = None

    yield  # 앱 실행 중

    # ── 종료 ────────────────────────────────────────────────────────────────
    if hasattr(app.state, "scheduler"):
        app.state.scheduler.shutdown(wait=False)
        logger.info("[Scheduler] APScheduler 종료")

    await close_db()
    logger.info("[DB] 커넥션 풀 해제")

    _stop_ssh_tunnel()


# =============================================================================
# FastAPI 앱 인스턴스 생성
# =============================================================================

app = FastAPI(
    title="withDOG API",
    description="반려견 동반 여행 및 AI 그림일기 서비스 withDOG 백엔드 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS 설정 ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# 공통 예외 핸들러
# =============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """처리되지 않은 예외를 500으로 변환합니다."""
    logger.error(f"[Unhandled Exception] {request.method} {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "서버 내부 오류가 발생했습니다."},
    )


# =============================================================================
# 라우터 등록
# 각 도메인 라우터는 구현 완료 후 주석을 해제하세요.
# =============================================================================

from routers import (
    admin_router,
    auth_router,
    breeds_router,
    chat_messages_router,
    chat_rooms_router,
    diaries_router,
    images_router,
    keywords_router,
    pets_router,
    users_router,
    places_router,
)

# 관리자 (영구 토큰 발급)
app.include_router(admin_router.router,         prefix="/admin",      tags=["Admin"])

# 인증 (소셜 로그인)
app.include_router(auth_router.router,          prefix="/auth",       tags=["Auth"])

# 사용자 (4순위) — /me 가 /{user_id} 보다 먼저 매칭되도록 순서 보장
app.include_router(users_router.router,         prefix="/users",      tags=["Users"])

# 반려견 (5순위)
app.include_router(pets_router.router,          prefix="/pets",       tags=["Pets"])

# 채팅방 + 채팅 메시지 (6순위) — 같은 prefix 공유
app.include_router(chat_rooms_router.router,    prefix="/chat-rooms", tags=["ChatRooms"])
app.include_router(chat_messages_router.router, prefix="/chat-rooms", tags=["ChatMessages"])

# 다이어리 (7순위)
app.include_router(diaries_router.router,       prefix="/diaries",    tags=["Diaries"])

# 이미지 (2순위)
app.include_router(images_router.router,        prefix="/images",     tags=["Images"])

# 견종 (3순위)
app.include_router(breeds_router.router,        prefix="/breeds",     tags=["Breeds"])

# 키워드 (온보딩 태그)
app.include_router(keywords_router.router,      prefix="/keywords",   tags=["Keywords"])

# 장소 검색 (Places)
app.include_router(places_router.router,       prefix="/places",       tags=["Places"])

# =============================================================================
# 헬스체크 엔드포인트
# =============================================================================

@app.get("/health", tags=["Health"], summary="서버 상태 확인")
async def health_check() -> dict:
    """서버 및 DB 연결 상태를 반환합니다."""

    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "status": "ok",
        "server": settings.SERVER,
        "db": db_status,
    }


# =============================================================================
# AI 일기 / 이미지 생성 엔드포인트 (구 루트 main.py)
# =============================================================================

_openai_client: AsyncOpenAI | None = None


def _get_openai_client() -> AsyncOpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


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


@app.post("/api/diary/generate", response_model=DiaryResponse, tags=["AI Diary"])
async def generate_diary(req: DiaryRequest) -> DiaryResponse:
    if not _AI_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI 모듈을 사용할 수 없습니다.")

    all_answers = req.main_answers + req.additional_answers
    conversation_summary = "\n".join(f"보호자: {a}" for a in all_answers if a.strip())
    if not conversation_summary:
        raise HTTPException(status_code=400, detail="답변 내용이 없습니다.")

    prompt = _diary_prompt_builder.build_diary_prompt(
    # prompt = build_diary_prompt(
        pet_name=req.pet_name,
        breed=req.breed,
        birth_date=req.birth_date,
        personalities=req.personalities,
        owner_name=req.owner_name,
        diary_type=req.diary_type,
        emotion=req.emotion_emoji,
        conversation_summary=conversation_summary,
    )

    response = await _get_openai_client().chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,   # 낮출수록 일관성↑ 창의성↓
        top_p=0.9,         # P값: 확률 상위 90% 토큰만 선택
        seed=42,           # 시드값: 동일 입력 시 재현 가능
        frequency_penalty=0.1,
    )

    raw = response.choices[0].message.content or ""
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail=f"LLM 응답 파싱 실패: {raw[:200]}")

    image_prompt = _diary_prompt_builder.build_final_image_prompt(
    # image_prompt = build_final_image_prompt(
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


@app.post("/api/diary/generate-image", response_model=ImageResponse, tags=["AI Diary"])
async def generate_image(req: ImageRequest) -> ImageResponse:
    if not _AI_AVAILABLE:
        raise HTTPException(status_code=503, detail="AI 모듈을 사용할 수 없습니다.")

    if not req.image_prompt.strip():
        raise HTTPException(status_code=400, detail="image_prompt가 비어 있습니다.")

    response = await _get_openai_client().images.generate(
        model="gpt-image-1",
        prompt=req.image_prompt,
        size="1024x1024",
        quality="medium",  # 옵션값: low→medium
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


if __name__ == "__main__":
    import uvicorn

    # uvicorn 실행 설정
    uvicorn.run(
        "main:app",     # 파일명:객체명
        host="0.0.0.0",
        port=8000,      # 포트 번호
        reload=True,    # 코드 수정 시 자동 재시작 (디버깅 시 유용)
        log_level="info"
    )
