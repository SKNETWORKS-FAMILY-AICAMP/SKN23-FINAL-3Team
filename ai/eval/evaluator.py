"""
ai/eval/evaluator.py
그림일기 이미지 생성 자동 평가 + 저장 모듈

저장 위치:
  ai/eval_data/evaluations.jsonl   ← 건별 전체 기록
  ai/eval_data/images/             ← 생성된 이미지 PNG
  ai/eval_data/summary.csv         ← 상세 로그용 CSV (기존 유지)
  ai/eval_data/summary_pretty.csv  ← 사람이 읽기 쉬운 요약 CSV (추가)

사용 흐름:
  [1] /api/diary/generate 호출
      → create_diary_session() 로 session_id 발급 + 두 프롬프트 저장

  [2] /api/diary/generate-image 호출
      → complete_image_eval() 로 이미지 저장 + 3개 메트릭 계산 + L0~L5 레벨 분류
"""

from __future__ import annotations

import base64
import csv
import io
import json
import uuid
from datetime import datetime
from pathlib import Path

from .metrics.subject_purity import score_subject_purity
from .metrics.bg_quality import score_bg_quality
from .metrics.style_consistency import score_style_consistency

# ── 경로 ──────────────────────────────────────────────────────────────────────
_AI_DIR = Path(__file__).parent.parent          # ai/
EVAL_DATA_DIR = _AI_DIR / "eval_data"
IMAGE_DIR = EVAL_DATA_DIR / "images"
JSONL_PATH = EVAL_DATA_DIR / "evaluations.jsonl"
CSV_PATH = EVAL_DATA_DIR / "summary.csv"
PRETTY_CSV_PATH = EVAL_DATA_DIR / "summary_pretty.csv"

# ── L0~L5 레벨 분류 규칙 ──────────────────────────────────────────────────────
#   총점(가중 합산) + 피사체/배경 감지 결과 조합

_LEVEL_LABELS = {
    0: "출력 실패",
    1: "저품질",
    2: "기본형",
    3: "확장형",
    4: "상호작용형",
    5: "완성형",
}

_LEVEL_VERDICTS = {
    0: "강아지 미검출 또는 생성 실패",
    1: "얼굴/배경 왜곡 또는 프롬프트 불일치가 있는 저품질 이미지",
    2: "강아지 한 마리가 중심인 단순한 장면",
    3: "강아지와 사물/배경 요소가 포함된 확장 장면",
    4: "강아지와 사람 또는 다른 요소가 함께 등장하는 복합 장면",
    5: "다양한 요소가 자연스럽게 어우러진 가장 풍부한 장면",
}

def classify_level(
    total_score: float | None,
    dog_detected: bool | None,
    human_detected: bool | None,
    bg_quality: float | None,
    subject_purity: float | None,
    style_consistency: float | None = None,
) -> int:
    """
    규칙 기반 L0~L5 분류.

    L0: total_score None / 강아지 미감지 / total_score < 20
    L1: total_score < 45 / bg_quality < 30 / style_consistency < 35 / subject_purity < 30
    L2: 강아지O, 사람X, bg_quality < 55
    L3: 강아지O, 사람X, bg_quality >= 55
    L4: 강아지O, 사람O, total_score < 80
    L5: 강아지O, 사람O, total_score >= 80
    """
    # L0: 출력 실패
    if total_score is None:
        return 0
    if dog_detected is False or total_score < 20:
        return 0

    # L1: 저품질
    if total_score < 45:
        return 1
    if bg_quality is not None and bg_quality < 30:
        return 1
    if style_consistency is not None and style_consistency < 35:
        return 1
    if subject_purity is not None and subject_purity < 30:
        return 1

    # L2 / L3: 사람 없음
    if human_detected is False:
        if bg_quality is not None and bg_quality < 55:
            return 2
        return 3

    # L4 / L5: 사람 있음
    if human_detected is True:
        if total_score < 80:
            return 4
        return 5

    # fallback
    return 2


# ── 가중 합산 ─────────────────────────────────────────────────────────────────
_WEIGHTS = {"subject_purity": 0.40, "bg_quality": 0.35, "style_consistency": 0.25}

def _weighted_total(sp: float | None, bq: float | None, sc: float | None) -> float | None:
    scores = {
        "subject_purity": sp,
        "bg_quality": bq,
        "style_consistency": sc,
    }
    valid = {k: v for k, v in scores.items() if v is not None}
    if not valid:
        return None
    weight_sum = sum(_WEIGHTS[k] for k in valid)
    total = sum(v * _WEIGHTS[k] for k, v in valid.items()) / weight_sum
    return round(total, 1)


# ── 이미지 저장 ───────────────────────────────────────────────────────────────
def _save_image(b64_str: str, session_id: str) -> str | None:
    try:
        from PIL import Image
        raw = base64.b64decode(b64_str)
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        path = IMAGE_DIR / f"{session_id}.png"
        img.save(path)
        return str(path)
    except Exception:
        return None


# ── CSV 초기화 ────────────────────────────────────────────────────────────────
_CSV_FIELDS = [
    # 식별
    "session_id", "timestamp", "pet_name", "breed", "emotion", "diary_type",
    # 레벨
    "level", "level_label",
    # 3대 메트릭
    "subject_purity", "bg_quality", "style_consistency", "total_score",
    # 세부
    "dog_detected", "human_detected", "extra_area_ratio",
    "brightness", "sharpness_estimate", "color_diversity",
    "style_similarity_raw", "reference_mode",
    # 프롬프트 요약
    "diary_prompt_length", "image_prompt_length",
    # 저장 경로
    "image_saved_path",
    # 수동 평가 (나중에 직접 기입)
    "manual_level", "manual_score", "notes",
]

def _ensure_dirs():
    EVAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)


# ── STEP 1: 일기 생성 시 호출 ─────────────────────────────────────────────────
def create_diary_session(
    diary_llm_prompt: str,
    image_prompt_base: str,
    image_prompt_final: str,
    diary_title: str = "",
    diary_content: str = "",
    diary_summary: str = "",
    pet_name: str = "",
    breed: str = "",
    breed_en: str = "",
    emotion: str = "",
    diary_type: str = "",
    personalities: list[str] | None = None,
) -> str:
    """
    일기 생성 직후 호출. session_id를 발급하고 두 프롬프트를 JSONL에 저장.
    이미지 생성 전 단계 — 메트릭은 아직 None.

    Returns: session_id (프론트에 넘겨서 generate-image 호출 시 재사용)
    """
    _ensure_dirs()

    session_id = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
    timestamp = datetime.now().isoformat()

    record = {
        "session_id": session_id,
        "timestamp": timestamp,
        # 펫 정보
        "pet_name": pet_name,
        "breed": breed,
        "breed_en": breed_en,
        "emotion": emotion,
        "diary_type": diary_type,
        "personalities": personalities or [],
        # ★ 두 프롬프트 전체 저장
        "diary_llm_prompt": diary_llm_prompt,
        "image_prompt_base": image_prompt_base,
        "image_prompt_final": image_prompt_final,
        # 일기 결과
        "diary_title": diary_title,
        "diary_content": diary_content,
        "diary_summary": diary_summary,
        # 이미지/메트릭 — 아직 미완
        "image_generated": False,
        "image_saved_path": None,
        # 3대 메트릭
        "subject_purity": None,
        "bg_quality": None,
        "style_consistency": None,
        "total_score": None,
        "level": None,
        "level_label": None,
        # 세부
        "dog_detected": None,
        "human_detected": None,
        "extra_area_ratio": None,
        "brightness": None,
        "sharpness_estimate": None,
        "color_diversity": None,
        "style_similarity_raw": None,
        "reference_mode": None,
        # 수동 평가 빈칸
        "manual_level": None,
        "manual_score": None,
        "notes": "",
    }

    with open(JSONL_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return session_id


# ── STEP 2: 이미지 생성 후 호출 ───────────────────────────────────────────────
def complete_image_eval(
    session_id: str,
    image_b64: str,
    image_prompt_final: str = "",
) -> dict:
    """
    이미지 생성 직후 호출.
    1) 이미지 파일 저장
    2) 3개 메트릭 계산
    3) L1~L5 레벨 분류
    4) JSONL 레코드 업데이트 + CSV 추가
    5) 결과 dict 반환

    session_id가 없으면 (단독 테스트) 자체 session 생성.
    """
    _ensure_dirs()

    # JSONL에서 기존 레코드 찾기
    record = _find_record(session_id)
    if record is None:
        # session 없이 이미지만 단독 평가하는 경우
        record = {
            "session_id": session_id or (
                datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]
            ),
            "timestamp": datetime.now().isoformat(),
            "pet_name": "", "breed": "", "emotion": "", "diary_type": "",
            "personalities": [],
            "diary_llm_prompt": "",
            "image_prompt_base": "",
            "image_prompt_final": image_prompt_final,
            "diary_title": "", "diary_content": "", "diary_summary": "",
            "image_generated": False,
            "image_saved_path": None,
            "subject_purity": None, "bg_quality": None, "style_consistency": None,
            "total_score": None, "level": None, "level_label": None,
            "dog_detected": None, "human_detected": None, "extra_area_ratio": None,
            "brightness": None, "sharpness_estimate": None, "color_diversity": None,
            "style_similarity_raw": None, "reference_mode": None,
            "manual_level": None, "manual_score": None, "notes": "",
        }

    # 이미지 저장
    image_path = _save_image(image_b64, record["session_id"])

    # 메트릭 계산
    prompt = image_prompt_final or record.get("image_prompt_final", "")
    sp_result = score_subject_purity(image_b64)
    bq_result = score_bg_quality(image_b64)
    sc_result = score_style_consistency(image_b64, prompt)

    sp = sp_result["subject_purity"]
    bq = bq_result["bg_quality"]
    sc = sc_result["style_consistency"]
    total = _weighted_total(sp, bq, sc)

    level = classify_level(
        total_score=total,
        dog_detected=sp_result["dog_detected"],
        human_detected=sp_result["human_detected"],
        bg_quality=bq,
        subject_purity=sp,
        style_consistency=sc,
    )

    # 레코드 업데이트
    record.update({
        "image_generated": True,
        "image_saved_path": image_path,
        # 3대 메트릭
        "subject_purity": sp,
        "bg_quality": bq,
        "style_consistency": sc,
        "total_score": total,
        "level": level,
        "level_label": _LEVEL_LABELS[level],
        # 세부
        "dog_detected": sp_result["dog_detected"],
        "human_detected": sp_result["human_detected"],
        "extra_area_ratio": sp_result["extra_area_ratio"],
        "brightness": bq_result["brightness"],
        "sharpness_estimate": bq_result["sharpness_estimate"],
        "color_diversity": bq_result["color_diversity"],
        "style_similarity_raw": sc_result["style_similarity_raw"],
        "reference_mode": sc_result["reference_mode"],
    })

    # JSONL 전체 재저장 (session_id 교체)
    _update_record(record)

    # CSV append
    _append_csv(record)
    _append_pretty_csv(record)

    return record


# ── 터미널 요약 출력 ──────────────────────────────────────────────────────────
def print_eval_summary(record: dict):
    level = record.get("level") or "?"
    label = record.get("level_label") or "-"
    sp = record.get("subject_purity")
    bq = record.get("bg_quality")
    sc = record.get("style_consistency")
    total = record.get("total_score")

    def fmt(v): return f"{v:.1f}" if v is not None else "N/A (라이브러리 없음)"

    print("\n" + "=" * 50)
    print(f"[그림일기 평가 결과]  session: {record.get('session_id', '-')}")
    print(f"  레벨      : {level} — {label}")
    print(f"  피사체순도 : {fmt(sp)} / 100  (가중치 40%)")
    print(f"  배경품질   : {fmt(bq)} / 100  (가중치 35%)")
    print(f"  스타일일관성: {fmt(sc)} / 100  (가중치 25%)")
    print(f"  ─────────────────────────────")
    print(f"  종합점수   : {fmt(total)} / 100")
    if record.get("image_saved_path"):
        print(f"  저장이미지 : {record['image_saved_path']}")
    print(f"  CSV       : {CSV_PATH}")
    print("=" * 50 + "\n")


# ── 내부 유틸 ─────────────────────────────────────────────────────────────────
def _find_record(session_id: str) -> dict | None:
    if not JSONL_PATH.exists():
        return None
    with open(JSONL_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
                if r.get("session_id") == session_id:
                    return r
            except json.JSONDecodeError:
                continue
    return None


def _update_record(updated: dict):
    """JSONL에서 같은 session_id 라인을 교체"""
    lines = []
    if JSONL_PATH.exists():
        with open(JSONL_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    if r.get("session_id") == updated["session_id"]:
                        lines.append(json.dumps(updated, ensure_ascii=False))
                    else:
                        lines.append(line)
                except json.JSONDecodeError:
                    lines.append(line)
    else:
        lines.append(json.dumps(updated, ensure_ascii=False))

    with open(JSONL_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _fmt_stability(dog_detected, total_score) -> str:
    """출력안정성: 강아지 감지 여부 + 종합점수 기반"""
    if not dog_detected:
        return "불안정"
    if total_score is None:
        return "불안정"
    if total_score >= 70:
        return "안정"
    if total_score >= 45:
        return "보통"
    return "불안정"


def _fmt_scene(bg_quality) -> str:
    """장면완성도: bg_quality 기반"""
    if bg_quality is None:
        return "N/A"
    if bg_quality >= 70:
        return "우수"
    if bg_quality >= 50:
        return "양호"
    if bg_quality >= 30:
        return "보통"
    return "미흡"


def _fmt_diary_fit(subject_purity, style_consistency) -> str:
    """그림일기적합성: subject_purity + style_consistency 평균"""
    vals = [v for v in [subject_purity, style_consistency] if v is not None]
    if not vals:
        return "N/A"
    avg = sum(vals) / len(vals)
    if avg >= 70:
        return "높음"
    if avg >= 50:
        return "보통"
    return "낮음"


_PRETTY_CSV_FIELDS = [
    "session_id", "생성시각", "반려견이름", "견종", "감정",
    "최종등급", "등급명", "종합점수",
    "출력안정성", "장면완성도", "그림일기적합성",
    "판정요약", "비고",
]


def _append_pretty_csv(record: dict):
    """사람이 읽기 쉬운 요약 CSV(summary_pretty.csv)에 한 행 추가"""
    pretty_exists = PRETTY_CSV_PATH.exists()

    level = record.get("level")
    level_int = level if isinstance(level, int) else None

    # 생성시각 포맷 정리 (ISO → 읽기 쉬운 형식)
    ts = record.get("timestamp", "")
    try:
        ts_fmt = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        ts_fmt = ts

    row = {
        "session_id": record.get("session_id", ""),
        "생성시각": ts_fmt,
        "반려견이름": record.get("pet_name", "") or "N/A",
        "견종": record.get("breed", "") or "N/A",
        "감정": record.get("emotion", "") or "N/A",
        "최종등급": f"L{level_int}" if level_int is not None else "N/A",
        "등급명": _LEVEL_LABELS.get(level_int, "N/A") if level_int is not None else "N/A",
        "종합점수": f"{record['total_score']:.1f}" if record.get("total_score") is not None else "N/A",
        "출력안정성": _fmt_stability(record.get("dog_detected"), record.get("total_score")),
        "장면완성도": _fmt_scene(record.get("bg_quality")),
        "그림일기적합성": _fmt_diary_fit(record.get("subject_purity"), record.get("style_consistency")),
        "판정요약": _LEVEL_VERDICTS.get(level_int, "알 수 없음") if level_int is not None else "알 수 없음",
        "비고": record.get("notes", "") or "",
    }

    with open(PRETTY_CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_PRETTY_CSV_FIELDS)
        if not pretty_exists:
            writer.writeheader()
        writer.writerow(row)


def _append_csv(record: dict):
    csv_exists = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_FIELDS)
        if not csv_exists:
            writer.writeheader()
        row = {
            "session_id": record.get("session_id", ""),
            "timestamp": record.get("timestamp", ""),
            "pet_name": record.get("pet_name", ""),
            "breed": record.get("breed", ""),
            "emotion": record.get("emotion", ""),
            "diary_type": record.get("diary_type", ""),
            "level": record.get("level", ""),
            "level_label": record.get("level_label", ""),
            "subject_purity": record.get("subject_purity", ""),
            "bg_quality": record.get("bg_quality", ""),
            "style_consistency": record.get("style_consistency", ""),
            "total_score": record.get("total_score", ""),
            "dog_detected": record.get("dog_detected", ""),
            "human_detected": record.get("human_detected", ""),
            "extra_area_ratio": record.get("extra_area_ratio", ""),
            "brightness": record.get("brightness", ""),
            "sharpness_estimate": record.get("sharpness_estimate", ""),
            "color_diversity": record.get("color_diversity", ""),
            "style_similarity_raw": record.get("style_similarity_raw", ""),
            "reference_mode": record.get("reference_mode", ""),
            "diary_prompt_length": len(record.get("diary_llm_prompt", "")),
            "image_prompt_length": len(record.get("image_prompt_final", "")),
            "image_saved_path": record.get("image_saved_path", ""),
            "manual_level": record.get("manual_level", ""),
            "manual_score": record.get("manual_score", ""),
            "notes": record.get("notes", ""),
        }
        writer.writerow(row)
