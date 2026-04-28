# -*- coding: utf-8 -*-
"""
ai/intent/data/_augment_alyojuseyo_samples.py
---------------------------------------------
'알려주세요' 종결어미 학습 데이터 보강 (2026-04-28).

KoELECTRA 가 `알려주세요` 종결어미를 '기타' 라벨과 강하게 연관지어 학습한
회귀 발견 (CSV 검증 기준 '알려주세요' 포함 3건이 모두 '기타'). 결과적으로
"○○ 전화번호 알려주세요" 같은 시설정보 발화도 '기타' 로 빠짐.

보강 전략:
    - 시설정보 +30: 시설명+속성+'알려주세요'. places 시드 시설명 활용.
    - 장소추천 +30: 지역+카테고리+'알려주세요'.
    - 다이어리 작성 +20: 가이드 요청 + 일기 작성 요청 + '알려주세요'.
    - 기타 +5: 도메인 외 일반 정보 요청 (균형용).

실행:
    python ai/intent/data/_augment_alyojuseyo_samples.py
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

RANDOM_SEED = 43  # 기존 facility augment 와 다른 시드 (중복 회피)

# ── 시설정보 패턴 (30개 목표) ────────────────────────────────
FACILITY_TEMPLATES = (
    "{name} 전화번호 알려주세요",
    "{name} 운영시간 알려주세요",
    "{name} 영업시간 알려주세요",
    "{name} 휴무일 알려주세요",
    "{name} 주소 알려주세요",
    "{name} 위치 알려주세요",
    "{name} 주차 가능한지 알려주세요",
    "{name} 입장료 알려주세요",
    "{name} 이용료 알려주세요",
    "{name} 연락처 알려주세요",
    "{name} 정보 알려주세요",
    "{name} 동반 조건 알려주세요",
)

# ── 장소추천 패턴 (30개 목표) ────────────────────────────────
PLACE_TEMPLATES = (
    "강아지랑 갈만한 {region} 카페 알려주세요",
    "{region} 반려견 동반 식당 알려주세요",
    "{region} 강아지랑 갈 곳 알려주세요",
    "주차 가능한 강아지 카페 알려주세요",
    "{region} 반려견 놀이터 알려주세요",
    "야외 테라스 있는 강아지 카페 알려주세요",
    "{region} 강아지 동반 호텔 알려주세요",
    "{region} 펜션 알려주세요",
    "조용한 반려견 카페 알려주세요",
    "{region} 강아지 산책 코스 알려주세요",
    "넓은 공원 알려주세요",
    "강아지랑 갈만한 곳 알려주세요",
    "{region} 강아지 동반 펜션 알려주세요",
    "반려견 동반 공원 알려주세요",
    "강아지 데려갈 카페 추천 알려주세요",
)

REGIONS = (
    "강남", "홍대", "이태원", "잠실", "여의도", "성수", "연남",
    "강북", "마포", "용산", "종로", "송파", "서초", "강서",
    "성북", "신촌", "건대", "압구정", "북촌", "한강",
)

# ── 다이어리 작성 패턴 (20개 목표) ────────────────────────────
DIARY_TEMPLATES = (
    "오늘 강아지랑 산책한 일기 써주는 방법 알려주세요",
    "그림일기 쓰는 방법 알려주세요",
    "강아지 일기 어떻게 쓰는지 알려주세요",
    "다이어리 작성하는 법 알려주세요",
    "그림일기 사용법 알려주세요",
    "오늘 우리 강아지 산책한 거 일기로 써주세요. 방법 알려주세요",
    "강아지 일기 쓰는 가이드 알려주세요",
    "그림일기 만드는 방법 알려주세요",
    "오늘의 다이어리 작성 방법 알려주세요",
    "강아지 일상 일기 쓰는 법 알려주세요",
    "추억 일기 작성하는 법 알려주세요",
    "다이어리 페이지 만드는 법 알려주세요",
    "그림일기 시작하는 방법 알려주세요",
    "강아지 사진 일기 작성법 알려주세요",
    "오늘 일기 쓰는 가이드 알려주세요",
    "강아지 다이어리 쓰는 절차 알려주세요",
    "AI 그림일기 사용법 알려주세요",
    "다이어리 기능 사용법 알려주세요",
    "오늘 강아지랑 한 일 일기로 정리하는 법 알려주세요",
    "강아지 추억 일기 만드는 법 알려주세요",
)

# ── 기타 +5 (균형용 도메인 외 정보 요청) ──────────────────────
ETC_EXTRA = (
    "이 앱 회원가입 방법 알려주세요",
    "구독 결제 취소하는 방법 알려주세요",
    "비밀번호 변경하는 방법 알려주세요",
    "앱 알림 설정 방법 알려주세요",
    "탈퇴하는 방법 알려주세요",
)


def _load_seoul_facility_names(n: int) -> list[str]:
    df = pd.read_csv(PLACES_CSV, encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    seoul = df[df["시도 명칭"] == "서울특별시"].copy()
    names = seoul["시설명"].dropna().drop_duplicates().tolist()
    random.shuffle(names)
    return names[:n]


def _build_rows() -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []

    # 시설정보 30 — 시설명 15개 × 평균 2 패턴
    facility_names = _load_seoul_facility_names(15)
    for name in facility_names:
        n_pat = random.choice([2, 3])
        for tmpl in random.sample(FACILITY_TEMPLATES, n_pat):
            rows.append((tmpl.format(name=name.strip()), "시설정보"))

    # 장소추천 30 — 지역 매칭 템플릿 + 지역 무관 템플릿
    for _ in range(30):
        tmpl = random.choice(PLACE_TEMPLATES)
        if "{region}" in tmpl:
            region = random.choice(REGIONS)
            rows.append((tmpl.format(region=region), "장소추천"))
        else:
            rows.append((tmpl, "장소추천"))

    # 다이어리 작성 20
    for tmpl in DIARY_TEMPLATES:
        rows.append((tmpl, "다이어리 작성"))

    # 기타 5
    for tmpl in ETC_EXTRA:
        rows.append((tmpl, "기타"))

    # 중복 제거
    return list(dict.fromkeys(rows))


def _append_to_target(rows: list[tuple[str, str]]) -> None:
    with open(TARGET_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\r\n")
        for text, label in rows:
            writer.writerow([text, label])


def main() -> None:
    random.seed(RANDOM_SEED)
    rows = _build_rows()
    print(f"[augment] 생성된 학습 행 수: {len(rows)}", file=sys.stderr)
    by_label: dict[str, int] = {}
    for _, lbl in rows:
        by_label[lbl] = by_label.get(lbl, 0) + 1
    for lbl, cnt in by_label.items():
        print(f"  {lbl}: {cnt}", file=sys.stderr)
    _append_to_target(rows)
    print(f"[augment] {TARGET_CSV} 에 append 완료", file=sys.stderr)


if __name__ == "__main__":
    main()
