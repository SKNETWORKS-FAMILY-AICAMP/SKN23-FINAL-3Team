FROM python:3.12-slim

# 시스템 패키지 (chromadb, ultralytics 등에 필요)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 의존성 먼저 설치 (캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 복사
# ai/ 폴더도 포함 (RAG, 임베딩 등)
COPY back/ ./back/
COPY ai/ ./ai/

# data/chroma_db도 필요하면 포함
# COPY data/ ./data/

WORKDIR /app/back

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]