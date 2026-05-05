# -*- coding: utf-8 -*-
"""
embed_places.py
---------------
places_merged.csv (문화정보원 21,098 + 관광공사 1,125 = 22,223행)를 읽어서
ChromaDB에 임베딩 적재하는 스크립트.

실행:
    cd data/embedding
    python embed_places.py

폴더 구조:
    (프로젝트 루트)/
    ├── chroma_db/
    ├── data/
    │   ├── embedding/
    │   │   └── embed_places.py   ← 여기서 실행
    │   └── processed/
    │       └── places_merged.csv
"""

import os
import uuid
import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ── 경로 설정 ──────────────────────────────────────────────
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH        = os.path.join(BASE_DIR, "processed", "places_merged.csv")
CHROMA_PATH     = os.path.join(BASE_DIR, "chroma_db")
COLLECTION_NAME = "dog_places"
MODEL_NAME      = "jhgan/ko-sroberta-multitask"
BATCH_SIZE      = 50


def _s(row, key: str) -> str:
    val = row.get(key)
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    return str(val).strip()


def _to_adj(val: str) -> str:
    """특징 값을 형용사형으로 변환.
    이미 형용사형(여유로운, 자연 친화적)이면 그대로 반환.
    """
    if not val:
        return val
    if val.endswith("함"):  return val[:-1] + "한"   # 아늑함→아늑한
    if val.endswith("참"):  return val[:-1] + "찬"   # 활기참→활기찬
    if val.endswith("빔"):  return val[:-1] + "비는"  # 붐빔→붐비는
    if val.endswith("음"):  return val[:-1] + "은"   # 넓음→넓은
    return val  # 여유로운, 자연 친화적, 보통 등 그대로


def build_embedding_text(row) -> str:
    """
    places_merged.csv 컬럼 기준으로 자연어 문장 생성.

    예시 출력:
      "피나클랜드 수목원은 충청남도에 위치한 관광지로 반려견 동반이 가능하다.
       반려견과 함께 조용하게 산책하기 좋은 장소이며 주차 공간이 넓고 무료로 제공된다.
       넓은 공간이다. 조용한 분위기다. 한적한 편이다. 숲 환경을 즐길 수 있다.
       주차 공간 등의 편의시설이 있다. 실외 이용 가능하다.
       운영시간은 연중무휴이다. 주차 가능하다."
    """
    name        = _s(row, "name")
    city        = _s(row, "city")
    sub_cat     = _s(row, "sub_category")
    desc        = _s(row, "장소설명")
    overview    = _s(row, "overview")
    space_size  = _s(row, "공간크기")
    vibe        = _s(row, "분위기")
    congestion  = _s(row, "혼잡도")
    nature      = _s(row, "자연환경")
    facility    = _s(row, "편의시설")
    access      = _s(row, "접근성")
    pet_restrict= _s(row, "pet_restrictions")
    size_limit  = _s(row, "pet_size_limit")
    open_hours  = _s(row, "open_hours")
    closed_days = _s(row, "closed_days")
    parking     = _s(row, "has_parking")
    extra_fee   = _s(row, "extra_fee_raw")
    is_indoor   = _s(row, "is_indoor")
    is_outdoor  = _s(row, "is_outdoor")

    parts = []

    # 1. 기본 소개
    if name and city and sub_cat:
        parts.append(f"{name}은 {city}에 위치한 {sub_cat}로 반려견 동반이 가능하다.")

    # 2. 장소 설명 (블로그 설명 우선, 없으면 overview)
    _invalid = {"아니오", "정보없음", "없음", "해당없음", ""}
    if desc and desc not in _invalid:
        parts.append(desc)
    elif overview:
        ov = overview[:500]
        if not ov.endswith("."): ov += "."
        parts.append(ov)

    # 3. 특징 문장 (형용사 변환 적용)
    if space_size:
        adj = _to_adj(space_size)
        parts.append(f"{adj} 공간이다.")
    if vibe:
        adj = _to_adj(vibe)
        parts.append(f"{adj} 분위기다.")
    if congestion:
        adj = _to_adj(congestion)
        parts.append(f"{adj} 편이다.")
    if nature:
        parts.append(f"{nature} 환경을 즐길 수 있다.")
    if facility:
        parts.append(f"{facility} 등의 편의시설이 있다.")
    if access:
        parts.append(f"{access}.")

    # 4. 실내외 여부
    if is_indoor in ("True", "true", "1") and is_outdoor in ("True", "true", "1"):
        parts.append("실내외 모두 이용 가능하다.")
    elif is_indoor in ("True", "true", "1"):
        parts.append("실내 이용 가능하다.")
    elif is_outdoor in ("True", "true", "1"):
        parts.append("실외 이용 가능하다.")

    # 5. 이용 조건 (첫 번째 조건만 사용, 긴 원문 그대로 추가)
    if pet_restrict and pet_restrict not in ["제한사항 없음", "해당없음"]:
        first_cond = pet_restrict.split("/")[0].strip()
        if first_cond:
            parts.append(f"이용 조건: {first_cond}.")
    if size_limit and size_limit not in ["모두 가능", "해당없음"]:
        parts.append(f"{size_limit} 입장 가능하다.")
    if extra_fee and extra_fee not in ["없음", "해당없음"]:
        parts.append(f"애견 동반 추가 요금은 {extra_fee}이다.")

    # 6. 운영 정보
    if open_hours:
        parts.append(f"운영시간은 {open_hours}이다.")
    if closed_days and closed_days not in ["해당없음"]:
        parts.append(f"휴무일은 {closed_days}이다.")
    if parking == "Y":
        parts.append("주차 가능하다.")
    elif parking == "N":
        parts.append("주차 불가하다.")

    return " ".join(parts)


def build_metadata(row) -> dict:
    def sf(key, default=0.0):
        try:
            v = row.get(key)
            return float(v) if pd.notna(v) else default
        except Exception:
            return default

    return {
        "content_id":   _s(row, "content_id"),
        "name":         _s(row, "name"),
        "category":     _s(row, "sub_category"),
        "city":         _s(row, "city"),
        "address":      _s(row, "address"),
        "lat":          sf("lat"),
        "lng":          sf("lng"),
        "indoor":       _s(row, "is_indoor"),
        "outdoor":      _s(row, "is_outdoor"),
        "conditions":   _s(row, "pet_restrictions"),
        "size_limit":   _s(row, "pet_size_limit") or "모두 가능",
        "open_hours":   _s(row, "open_hours") or "운영 시간 미제공 · 방문 전 문의 권장",
        "closed_days":  _s(row, "closed_days"),
        "parking":      _s(row, "has_parking"),
        "tel":          _s(row, "tel"),
        "homepage":     _s(row, "homepage"),
        "extra_fee":    _s(row, "extra_fee_raw") or "없음",
        "entrance_fee": _s(row, "entrance_fee_raw"),
        "source":       _s(row, "source"),
    }


def main():
    # 1. CSV 로드
    print(f"CSV 로딩: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    print(f"  전체 행 수: {len(df)}")

    df = df.dropna(subset=["name", "lat", "lng"])
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df = df.dropna(subset=["lat", "lng"])
    print(f"  정제 후: {len(df)}행")

    # 2. 임베딩 모델 로드
    print(f"\n임베딩 모델 로딩: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("  모델 로딩 완료!")

    # 3. ChromaDB 연결
    print(f"\nChromaDB 연결: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"  기존 '{COLLECTION_NAME}' 컬렉션 삭제")
    except Exception:
        print(f"  기존 컬렉션 없음, 새로 생성")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"  '{COLLECTION_NAME}' 컬렉션 생성 완료")

    # 4. 텍스트 생성
    print("\n임베딩 텍스트 생성 중...")
    texts, metadatas, ids = [], [], []
    for _, row in df.iterrows():
        text = build_embedding_text(row)
        if not text.strip():
            continue
        texts.append(text)
        metadatas.append(build_metadata(row))
        ids.append(str(uuid.uuid4()))

    print(f"  생성 완료: {len(texts)}개")

    # 샘플 출력
    print("\n샘플 임베딩 텍스트 (특징 있는 행 2개):")
    feat_rows = df[df["장소설명"].notna()].head(2)
    for _, row in feat_rows.iterrows():
        print(f"  [{_s(row, 'name')}]")
        print(f"  {build_embedding_text(row)}")
        print()

    # 5. 배치 임베딩 & 적재
    print(f"ChromaDB 적재 시작 (배치 크기: {BATCH_SIZE})")
    total = len(texts)
    for start in tqdm(range(0, total, BATCH_SIZE), desc="적재 중"):
        end = min(start + BATCH_SIZE, total)
        batch_texts     = texts[start:end]
        batch_metadatas = metadatas[start:end]
        batch_ids       = ids[start:end]

        embeddings = model.encode(batch_texts, show_progress_bar=False).tolist()
        collection.add(
            ids=batch_ids,
            embeddings=embeddings,
            documents=batch_texts,
            metadatas=batch_metadatas,
        )

    print(f"\n적재 완료! 총 {collection.count()}개 저장됨")
    print(f"저장 위치: {CHROMA_PATH}")

    # 6. 검색 테스트
    print("\n검색 테스트:")
    test_queries = [
        "조용한 공원 강아지 산책",
        "아늑한 실내 카페",
        "넓고 한적한 야외 장소",
        "숲 속 자연 환경",
        "주차 가능한 펜션",
    ]
    for query in test_queries:
        emb = model.encode(query).tolist()
        results = collection.query(query_embeddings=[emb], n_results=3)
        print(f"\n  쿼리: '{query}'")
        for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
            print(f"    → {meta.get('name')} ({meta.get('category')}, {meta.get('city')})")
            print(f"       {doc[:80]}...")


if __name__ == "__main__":
    main()
