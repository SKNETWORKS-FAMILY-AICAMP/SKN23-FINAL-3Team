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
#   1) torch 를 CPU-only wheel 인덱스에서 먼저 설치
#      (기본 PyPI wheel 은 CUDA 런타임 포함 → 이미지 2~3GB 팽창 원인).
#   2) 이어서 requirements.txt(운영 전용) 설치. pip 는 이미 설치된
#      CPU torch 가 범위를 만족하면 그대로 두므로 CUDA wheel 로 덮어쓰지 않음.
#   * 같은 RUN 블록 안에 두 단계를 묶어 pip BuildKit 캐시 마운트를 공유.
#   * 학습/개발 전용(requirements-dev.txt)은 운영 이미지에 포함하지 않는다.
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision \
    && pip install -r requirements.txt

# 소스 복사
# ai/ 폴더도 포함 (RAG, 임베딩 등)
COPY back/ ./back/
COPY ai/ ./ai/

# data/chroma_db도 필요하면 포함
# COPY data/ ./data/

WORKDIR /app/back

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
