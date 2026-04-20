"""
withDOG 챗봇 의도 분류기 - KoELECTRA 파인튜닝
사전학습 모델: monologg/koelectra-base-v3-discriminator
"""
import os
import shutil
import tempfile
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    ElectraTokenizer,
    ElectraForSequenceClassification,
    get_linear_schedule_with_warmup
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import json

CONFIG = {
    "model_name": "monologg/koelectra-base-v3-discriminator",
    "data_path": "./data/sample_data.csv",
    "save_dir": "./model",
    "max_length": 128,
    "batch_size": 16,
    "epochs": 5,
    "learning_rate": 3e-5,
    "test_size": 0.2,
    "seed": 42,
}

LABELS = ["다이어리 작성", "장소추천", "시설정보", "기타"]
LABEL2ID = {label: idx for idx, label in enumerate(LABELS)}
ID2LABEL = {idx: label for idx, label in enumerate(LABELS)}


class IntentDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt"
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "token_type_ids": encoding["token_type_ids"].squeeze(),
            "labels": torch.tensor(self.labels[idx], dtype=torch.long)
        }


def load_data(data_path):
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["text", "label"])
    df = df[df["label"].isin(LABELS)].reset_index(drop=True)
    texts = df["text"].tolist()
    labels = [LABEL2ID[label] for label in df["label"].tolist()]
    print(f"전체 데이터 수: {len(texts)}")
    print(f"카테고리 분포:\n{df['label'].value_counts()}\n")
    return texts, labels


def train(model, dataloader, optimizer, scheduler, device):
    model.train()
    total_loss = 0
    for batch in dataloader:
        optimizer.zero_grad()
        input_ids = batch["input_ids"].to(device)
        attention_mask = batch["attention_mask"].to(device)
        token_type_ids = batch["token_type_ids"].to(device)
        labels = batch["labels"].to(device)
        outputs = model(input_ids=input_ids, attention_mask=attention_mask,
                        token_type_ids=token_type_ids, labels=labels)
        loss = outputs.loss
        total_loss += loss.item()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
    return total_loss / len(dataloader)


def evaluate(model, dataloader, device):
    model.eval()
    predictions, true_labels = [], []
    with torch.no_grad():
        for batch in dataloader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            token_type_ids = batch["token_type_ids"].to(device)
            labels = batch["labels"].to(device)
            outputs = model(input_ids=input_ids, attention_mask=attention_mask,
                            token_type_ids=token_type_ids)
            preds = torch.argmax(outputs.logits, dim=-1)
            predictions.extend(preds.cpu().numpy())
            true_labels.extend(labels.cpu().numpy())
    return predictions, true_labels


def main():
    torch.manual_seed(CONFIG["seed"])
    np.random.seed(CONFIG["seed"])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"사용 디바이스: {device}\n")

    texts, labels = load_data(CONFIG["data_path"])
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, labels, test_size=CONFIG["test_size"],
        random_state=CONFIG["seed"], stratify=labels
    )
    print(f"학습 데이터: {len(train_texts)}건 | 검증 데이터: {len(val_texts)}건\n")

    print("KoELECTRA 모델 로딩 중...")
    tokenizer = ElectraTokenizer.from_pretrained(CONFIG["model_name"])
    model = ElectraForSequenceClassification.from_pretrained(
        CONFIG["model_name"], num_labels=len(LABELS),
        id2label=ID2LABEL, label2id=LABEL2ID
    )
    model.to(device)

    train_dataset = IntentDataset(train_texts, train_labels, tokenizer, CONFIG["max_length"])
    val_dataset = IntentDataset(val_texts, val_labels, tokenizer, CONFIG["max_length"])
    train_loader = DataLoader(train_dataset, batch_size=CONFIG["batch_size"], shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=CONFIG["batch_size"])

    optimizer = torch.optim.AdamW(model.parameters(), lr=CONFIG["learning_rate"])
    total_steps = len(train_loader) * CONFIG["epochs"]
    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=total_steps // 10, num_training_steps=total_steps
    )

    best_accuracy = 0
    print("=" * 50 + "\n학습 시작\n" + "=" * 50)
    for epoch in range(CONFIG["epochs"]):
        train_loss = train(model, train_loader, optimizer, scheduler, device)
        preds, true_labels_list = evaluate(model, val_loader, device)
        accuracy = sum(p == t for p, t in zip(preds, true_labels_list)) / len(true_labels_list)
        print(f"Epoch {epoch+1}/{CONFIG['epochs']} | Loss: {train_loss:.4f} | Accuracy: {accuracy:.4f}")

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            # 임시 디렉터리에 저장 후 교체 (Windows 파일 잠금 우회)
            tmp_dir = tempfile.mkdtemp()
            try:
                model.save_pretrained(tmp_dir)
                tokenizer.save_pretrained(tmp_dir)
                with open(os.path.join(tmp_dir, "label_map.json"), "w", encoding="utf-8") as f:
                    json.dump({"id2label": ID2LABEL, "label2id": LABEL2ID}, f, ensure_ascii=False, indent=2)
                if os.path.exists(CONFIG["save_dir"]):
                    shutil.rmtree(CONFIG["save_dir"])
                shutil.copytree(tmp_dir, CONFIG["save_dir"])
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
            print(f"  → 최고 성능 모델 저장 완료 (Accuracy: {best_accuracy:.4f})")

    print("\n" + "=" * 50 + "\n최종 평가 리포트\n" + "=" * 50)
    preds, true_labels_list = evaluate(model, val_loader, device)
    print(classification_report(true_labels_list, preds, target_names=LABELS, digits=4))


if __name__ == "__main__":
    main()
