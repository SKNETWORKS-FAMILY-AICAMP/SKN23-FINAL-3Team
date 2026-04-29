import torch
import json
from transformers import ElectraTokenizer, ElectraForSequenceClassification

MODEL_DIR = "./model"


def load_model():
    tokenizer = ElectraTokenizer.from_pretrained(MODEL_DIR)
    model = ElectraForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    with open(f"{MODEL_DIR}/label_map.json", "r", encoding="utf-8") as f:
        label_map = json.load(f)
    return tokenizer, model, label_map["id2label"]


def predict(text, tokenizer, model, id2label):
    encoding = tokenizer(text, max_length=128, padding="max_length",
                         truncation=True, return_tensors="pt")
    with torch.no_grad():
        outputs = model(**encoding)
        probs = torch.softmax(outputs.logits, dim=-1)[0]
        pred_id = torch.argmax(probs).item()
    return {
        "intent": id2label[str(pred_id)],
        "confidence": round(probs[pred_id].item(), 4),
        "all_probs": {id2label[str(i)]: round(p.item(), 4) for i, p in enumerate(probs)}
    }


if __name__ == "__main__":
    tokenizer, model, id2label = load_model()
    test_cases = [
        "강아지랑 갈 수 있는 홍대 카페 알려줘",
        "오늘 강아지 일기 써줘",
        "이 카페 울타리 있어?",
        "반려견 동반 식당 추천해줘",
        "여기 소형견만 되나요?",
    ]
    for text in test_cases:
        result = predict(text, tokenizer, model, id2label)
        print(f"입력: {text}")
        print(f"  → 예측: {result['intent']} (확신도: {result['confidence']:.2%})")
        print(f"  → 전체 확률: {result['all_probs']}\n")
