# -*- coding: utf-8 -*-
"""
ai/intent/data/_lint_samples.py
-------------------------------
sample_data.csv 의 중복/유사/노이즈 검증 (read-only).

검증 항목:
    1. 정확 중복 (text 가 byte 단위 동일) — 즉시 제거 후보
    2. 라벨 불일치 중복 (같은 text, 다른 label) — 학습 노이즈
    3. 정규화 중복 (공백·구두점·종결어미 mark 제거 후 동일) — 사실상 같은 발화
    4. 패턴 over-representation (시설명/지역명 토큰 마스킹 후 빈도)

결과는 stderr 로 텍스트 출력 (콘솔 인코딩 mojibake 회피용으로
파일 출력 옵션도 제공).
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter, defaultdict

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
TARGET_CSV = os.path.join(_HERE, "sample_data.csv")
OUTPUT = os.path.join(_HERE, "_lint_report.txt")


def _normalize(text: str) -> str:
    """공백·구두점·종결어미 mark 제거 → 비교용 키."""
    t = text.strip().lower()
    t = re.sub(r"\s+", "", t)
    t = re.sub(r"[?!.,~ㅋㅎㅠㅜ]+", "", t)
    return t


def _mask_named_entities(text: str) -> str:
    """시설명·지역명을 마스킹해서 패턴만 추출.

    완벽한 NER 은 불가능하므로 휴리스틱:
    - 한글 명사 연속 2~10자 → <NAME>
    - 일부 흔한 지역명 키워드도 마스킹
    """
    t = text
    region_keywords = (
        "서울", "강남", "강북", "강서", "강동", "마포", "용산", "종로", "중구",
        "송파", "서초", "관악", "동작", "영등포", "성동", "성북", "노원", "도봉",
        "은평", "서대문", "동대문", "광진", "구로", "금천", "양천", "중랑",
        "잠실", "홍대", "이태원", "신촌", "여의도", "건대", "신림", "수유", "쌍문",
        "압구정", "청담", "성수", "연남", "망원", "합정", "북촌", "경복궁", "한강",
    )
    for region in region_keywords:
        t = t.replace(region, "<REGION>")
    # 한글 2~10자 연속을 NAME 후보로 (이미 REGION 처리된 곳 제외)
    return t


def main() -> None:
    df = pd.read_csv(TARGET_CSV, encoding="utf-8")
    df["text"] = df["text"].astype(str)
    df["label"] = df["label"].astype(str)

    out_lines: list[str] = []

    out_lines.append(f"총 행 수: {len(df)}")
    out_lines.append("")
    out_lines.append("라벨 분포:")
    for lbl, cnt in df["label"].value_counts().items():
        out_lines.append(f"  {lbl}: {cnt}")
    out_lines.append("")

    # 1. 정확 중복 (text 완전 동일)
    exact_dups = df[df.duplicated(subset=["text"], keep=False)].sort_values("text")
    out_lines.append(f"=== [1] 정확 중복 (text 동일): {len(exact_dups)}건 ===")
    if len(exact_dups) > 0:
        groups = exact_dups.groupby("text")
        for text, grp in groups:
            labels = list(grp["label"].values)
            out_lines.append(f"  '{text}' × {len(grp)}건 / labels={labels}")
    out_lines.append("")

    # 2. 라벨 불일치 중복 (같은 text, 다른 label)
    label_conflicts = []
    for text, grp in df.groupby("text"):
        unique_labels = grp["label"].unique()
        if len(unique_labels) > 1:
            label_conflicts.append((text, list(unique_labels), len(grp)))
    out_lines.append(f"=== [2] 라벨 불일치 중복: {len(label_conflicts)}건 ===")
    for text, labels, count in label_conflicts:
        out_lines.append(f"  '{text}' / labels={labels} / count={count}")
    out_lines.append("")

    # 3. 정규화 중복 (공백·구두점 제거 후 동일)
    norm_groups: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for _, row in df.iterrows():
        norm = _normalize(row["text"])
        norm_groups[norm].append((row["text"], row["label"]))
    norm_dups = {k: v for k, v in norm_groups.items() if len(v) > 1}
    out_lines.append(f"=== [3] 정규화 중복 (정확 중복 포함): {len(norm_dups)}그룹 ===")
    for norm_key, items in sorted(norm_dups.items(), key=lambda x: -len(x[1])):
        if len(items) < 2:
            continue
        out_lines.append(f"  norm='{norm_key}' × {len(items)}건")
        for text, label in items:
            out_lines.append(f"    - '{text}' [{label}]")
    out_lines.append("")

    # 4. 패턴 over-representation
    pattern_counter: Counter[str] = Counter()
    for _, row in df.iterrows():
        masked = _mask_named_entities(row["text"])
        pattern_counter[(row["label"], masked)] += 1
    out_lines.append(f"=== [4] 같은 (라벨, 마스킹된 패턴) 5건 이상 ===")
    over_rep = [
        (lbl_pat, cnt) for lbl_pat, cnt in pattern_counter.items() if cnt >= 5
    ]
    over_rep.sort(key=lambda x: -x[1])
    for (label, pattern), count in over_rep[:30]:
        out_lines.append(f"  [{label}] '{pattern}' × {count}건")
    out_lines.append("")

    # 빈 행/이상한 라벨 체크
    out_lines.append("=== [5] 라벨 오타/이상치 ===")
    expected = {"다이어리 작성", "장소추천", "시설정보", "기타"}
    bad = df[~df["label"].isin(expected)]
    out_lines.append(f"  비표준 라벨: {len(bad)}건")
    for _, row in bad.iterrows():
        out_lines.append(f"    - text='{row['text']}' label='{row['label']}'")
    out_lines.append("")

    out_lines.append("=== [6] 빈 text 체크 ===")
    empty = df[df["text"].str.strip() == ""]
    out_lines.append(f"  빈 text: {len(empty)}건")
    out_lines.append("")

    report = "\n".join(out_lines)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"보고서 저장: {OUTPUT}", file=sys.stderr)
    # 핵심 요약만 stderr
    print(f"정확중복={len(exact_dups)} 라벨불일치={len(label_conflicts)} "
          f"정규화중복={len(norm_dups)}그룹 패턴과대표={len(over_rep)}패턴", file=sys.stderr)


if __name__ == "__main__":
    main()
