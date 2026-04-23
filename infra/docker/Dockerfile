# syntax=docker/dockerfile:1.6
FROM python:3.12-slim

# 시스템 패키지 (chromadb, ultralytics 등에 필요)
# apt 캐시는 BuildKit 캐시 마운트로 유지 → 재빌드 시 다시 다운로드 안 함.
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libgl1 \
        libglib2.0-0

WORKDIR /app

# 의존성 설치.
#   1) requirements.txt 내용이 그대로면 이 레이어 자체가 캐시 히트로 skip.
#   2) 캐시가 무효화돼 재설치해야 하더라도 BuildKit pip wheel 캐시(/root/.cache/pip)
#      가 유지되므로 PyPI 재다운로드 없이 수 배 빠르게 완료.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install -r requirements.txt

# 소스 복사
# ai/ 폴더도 포함 (RAG, 임베딩 등)
COPY back/ ./back/
COPY ai/ ./ai/

# data/chroma_db도 필요하면 포함
# COPY data/ ./data/

WORKDIR /app/back

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
