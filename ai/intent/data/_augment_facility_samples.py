# -*- coding: utf-8 -*-
"""
ai/intent/data/_augment_facility_samples.py
-------------------------------------------
시설정보 학습 데이터 보강 스크립트 (2026-04-28).

KoELECTRA 의도분류기가 "○○ 전화번호", "○○ 운영시간" 같은
시설명 + 속성 질문 패턴을 장소추천으로 오분류하는 회귀 해소를 위해
실제 places 시드 CSV 의 서울 시설명을 샘플링해 다양한 발화 패턴을
생성, `sample_data.csv` 에 append.

실행:
    python ai/intent/data/_augment_facility_samples.py

재실행 시 동일 random_state 로 같은 결과가 나오므로 중복 append 주의.
"""
from __future__ import annotations

import csv
import os
import random
import sys

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_HERE, "../../.."))

PLACES_CSV = os.path.join(
    _REPO_ROOT,
    "data/raw/한국문화정보원_전국_반려동물_동반_가능_문화시설_위치_데이터_20250324.csv",
)
TARGET_CSV = os.path.join(_HERE, "sample_data.csv")

RANDOM_SEED = 42
TARGET_FACILITY_COUNT = 50          # 샘플링할 고유 시설명 수
MIN_PATTERNS_PER_FACILITY = 2       # 시설별 최소 패턴
MAX_PATTERNS_PER_FACILITY = 3       # 시설별 최대 패턴

PATTERNS: tuple[str, ...] = (
    # 전화·연락처
    "{name} 전화번호 알려줘",
    "{name} 전화번호 뭐야?",
    "{name} 전화번호 좀 알려줘",
    "{name} 연락처 알려줘",
    "{name} 연락처 어떻게 돼?",
    # 운영시간·휴무
    "{name} 운영시간 알려줘",
    "{name} 영업시간 알려줘",
    "{name} 몇시까지 해?",
    "{name} 몇 시에 문 열어?",
    "{name} 주말에도 열어?",
    "{name} 휴무일 언제야?",
    "{name} 쉬는 날 알려줘",
    "{name} 연중무휴야?",
    # 주차
    "{name} 주차 가능해?",
    "{name} 주차장 있어?",
    "{name} 주차 돼?",
    # 위치·주소
    "{name} 위치 어디야?",
    "{name} 어디 있어?",
    "{name} 주소 알려줘",
    "{name} 어디로 가야 해?",
    # 입장료
    "{name} 입장료 얼마야?",
    "{name} 이용료 얼마야?",
    "{name} 입장료 있어?",
    # 실내외
    "{name} 실내 이용 가능해?",
    "{name} 야외 있어?",
    "{name} 테라스 있어?",
    # 동반 조건
    "{name} 목줄 필수야?",
    "{name} 강아지 동반 조건 알려줘",
    "{name} 반려견 데려가도 돼?",
)


def _load_seoul_places() -> pd.DataFrame:
    df = pd.read_csv(PLACES_CSV, encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    seoul = df[df["시도 명칭"] == "서울특별시"].copy()
    return seoul.dropna(subset=["시설명"])


def _stratified_facility_names(seoul: pd.DataFrame, total: int) -> list[str]:
    """카테고리3 별로 골고루 시설명을 샘플링한다.

    `카테고리3` 분포가 매우 편향되어 있으므로(반려의료가 압도적), 각 카테고리에서
    최소 1개, 최대 비율 기반 N개를 뽑아 다양성을 확보한다.
    """
    cat_counts = seoul["카테고리3"].dropna().value_counts()
    names: list[str] = []
    for cat, count in cat_counts.items():
        # 비율 기반: 큰 카테고리는 더 많이, 작은 카테고리도 최소 1개
        per_cat = max(1, min(8, count // 200))
        cat_rows = seoul[seoul["카테고리3"] == cat]
        unique_names = cat_rows["시설명"].drop_duplicates()
        if unique_names.empty:
            continue
        n = min(per_cat, len(unique_names))
        sampled = unique_names.sample(n, random_state=RANDOM_SEED).tolist()
        names.extend(sampled)
        if len(names) >= total * 1.5:
            break
    # 중복 제거 + 셔플 후 target 수만큼 자름
    deduped = list(dict.fromkeys(names))
    random.shuffle(deduped)
    return deduped[:total]


def _build_training_rows(facility_names: list[str]) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for name in facility_names:
        n_patterns = random.choice(
            list(range(MIN_PATTERNS_PER_FACILITY, MAX_PATTERNS_PER_FACILITY + 1))
        )
        chosen = random.sample(PATTERNS, n_patterns)
        for tmpl in chosen:
            rows.append((tmpl.format(name=name.strip()), "시설정보"))
    # 중복 제거 (시설명+패턴 충돌 방어)
    return list(dict.fromkeys(rows))


def _append_to_target(rows: list[tuple[str, str]]) -> None:
    with open(TARGET_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\r\n")
        for text, label in rows:
            writer.writerow([text, label])


def main() -> None:
    random.seed(RANDOM_SEED)
    seoul = _load_seoul_places()
    print(f"[augment] 서울 시설 수: {len(seoul)}", file=sys.stderr)

    names = _stratified_facility_names(seoul, TARGET_FACILITY_COUNT)
    print(f"[augment] 샘플링된 고유 시설명: {len(names)}", file=sys.stderr)

    rows = _build_training_rows(names)
    print(f"[augment] 생성된 학습 행 수: {len(rows)}", file=sys.stderr)

    _append_to_target(rows)
    print(f"[augment] {TARGET_CSV} 에 append 완료", file=sys.stderr)


if __name__ == "__main__":
    main()
