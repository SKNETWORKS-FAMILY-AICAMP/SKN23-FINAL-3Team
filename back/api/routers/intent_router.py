# withDOG 챗봇 의도 분류 라우터
# 모델 위치: ai/intent/model/
import os
import json
import torch
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import ElectraTokenizer, ElectraForSequenceClassification
from dotenv import load_dotenv

load_dotenv()

_DEFAULT_MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "ai", "intent", "model")
)
MODEL_DIR = os.getenv("INTENT_MODEL_DIR", _DEFAULT_MODEL_DIR)

if not os.path.isdir(MODEL_DIR):
    raise FileNotFoundError(
        f"의도 분류 모델 폴더가 없습니다: {MODEL_DIR}\n"
        f"먼저 학습을 실행하세요: cd ai/intent && python train.py"
    )

_tokenizer = None
_model = None
_id2label = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tokenizer, _model, _id2label
    _tokenizer = ElectraTokenizer.from_pretrained(MODEL_DIR)
    _model = ElectraForSequenceClassification.from_pretrained(MODEL_DIR)
    _model.eval()
    with open(f"{MODEL_DIR}/label_map.json", "r", encoding="utf-8") as f:
        _id2label = json.load(f)["id2label"]
    print("의도 분류 모델 로딩 완료!")
    yield


app = FastAPI(title="withDOG 의도 분류 API", lifespan=lifespan)

RAG_STRATEGY_MAP = {
    "다이어리 작성": {"collection": "diary",  "top_k": 3,
                      "description": "강아지 행동 과학 지식 검색 → 감정 추론 → 강아지 시점 일기 생성"},
    "장소추천":      {"collection": "places", "top_k": 5,
                      "description": "반려견 동반 가능 장소 데이터베이스 검색"},
    "시설정보":      {"collection": "places", "top_k": 1,
                      "description": "특정 시설 상세 정보 검색"},
}


class ChatRequest(BaseModel):
    query: str
    user_id: str | None = None


class IntentResponse(BaseModel):
    intent: str
    confidence: float
    rag_strategy: dict
    query: str


def classify_intent(text):
    encoding = _tokenizer(text, max_length=128, padding="max_length", truncation=True, return_tensors="pt")
    with torch.no_grad():
        probs = torch.softmax(_model(**encoding).logits, dim=-1)[0]
        pred_id = torch.argmax(probs).item()
    return _id2label[str(pred_id)], round(probs[pred_id].item(), 4)


@app.post("/chat/classify", response_model=IntentResponse)
async def classify_chat_intent(request: ChatRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="쿼리가 비어 있습니다.")
    intent, confidence = classify_intent(request.query)
    return IntentResponse(
        intent=intent,
        confidence=confidence,
        rag_strategy=RAG_STRATEGY_MAP.get(intent, RAG_STRATEGY_MAP["장소추천"]),
        query=request.query,
    )


@app.get("/health")
async def health_check():
    return {"status": "ok", "model_loaded": _model is not None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("intent_router:app", host="0.0.0.0", port=8001, reload=False)
