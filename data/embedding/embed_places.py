# -*- coding: utf-8 -*-
"""
embed_places.py
---------------
반려동물_동반가능_장소_완성.csv를 읽어서
ChromaDB에 임베딩 적재하는 스크립트

실행 위치: vector/embedding/ 폴더에서 실행
    cd vector/embedding
    python embed_places.py

폴더 구조:
    vector/
    ├── chroma_db/
    ├── data/
    │   └── processed/
    │       └── 반려동물_동반가능_장소_완성.csv
    └── embedding/
        └── embed_places.py   ← 여기서 실행

적재 전략:
    여러 칼럼을 자연어 한 문장으로 구성해서 임베딩
    예) "반포 한강공원은 서울특별시 서초구에 위치한 공원으로
        넓고 잘 관리된 산책로가 있어 반려견과 함께 걷기에 좋은 분위기다.
        넓음 공간 아늑함 분위기 강변을 즐길 수 있다.
        대중교통으로 접근하기 좋다. 실외 이용 가능하다.
        목줄, 배변봉투이 필요하다. 운영시간은 매일 00:00~24:00이다."
"""

import os
import uuid
import chromadb
import pandas as pd
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

# ── 경로 설정 ─────────────────────────────────────────────
# embedding/ 폴더에서 실행하므로 한 단계 위(vector/)를 BASE_DIR로 설정
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH    = os.path.join(BASE_DIR, "processed", "반려동물_동반가능_장소_완성.csv")
CHROMA_PATH = os.path.join(BASE_DIR, "chroma_db")

# ── ChromaDB 설정 ─────────────────────────────────────────
COLLECTION_NAME = "dog_places"
MODEL_NAME      = "jhgan/ko-sroberta-multitask"

# ── 배치 크기 ─────────────────────────────────────────────
BATCH_SIZE = 50


def build_embedding_text(row: pd.Series) -> str:
    """
    여러 칼럼을 자연어 한 문장으로 합쳐서 임베딩용 텍스트 생성.
    의미 기반 검색이 잘 되도록 문장 형태로 구성.
    """
    def s(key):
        val = row.get(key)
        return str(val) if pd.notna(val) and str(val).strip() else ""

    name        = s("시설명")
    category    = s("카테고리3")
    city        = s("시도 명칭")
    district    = s("시군구 명칭")
    desc        = s("장소설명")
    base_desc   = s("기본 정보_장소설명")
    space_size  = s("공간크기")
    vibe        = s("분위기")
    congestion  = s("혼잡도")
    nature      = s("자연환경")
    access      = s("접근성")
    facility    = s("편의시설")
    conditions  = s("반려동물 제한사항")
    size_hint   = s("입장 가능 동물 크기")
    open_hours  = s("운영시간")
    closed_days = s("휴무일")
    parking     = s("주차 가능여부")
    extra_fee   = s("애견 동반 추가 요금")
    indoor      = s("장소(실내) 여부")
    outdoor     = s("장소(실외)여부")

    parts = []

    # ── 기본 소개 ──────────────────────────────────────────
    location = " ".join(filter(None, [city, district]))
    if name and category and location:
        parts.append(f"{name}은 {location}에 위치한 {category}으로")

    # ── 장소 설명 ──────────────────────────────────────────
    if desc:
        parts.append(desc)
    elif base_desc:
        parts.append(base_desc)

    # ── 특징 문장 ──────────────────────────────────────────
    features = []
    if space_size:
        features.append(f"{space_size} 공간")
    if vibe:
        features.append(f"{vibe} 분위기")
    if nature:
        features.append(f"{nature}을 즐길 수 있다")
    if congestion:
        features.append(f"{congestion} 편이다")
    if features:
        parts.append(" ".join(features) + ".")

    # ── 접근성 ────────────────────────────────────────────
    if access:
        parts.append(f"{access}으로 접근하기 좋다.")

    # ── 편의시설 ──────────────────────────────────────────
    if facility:
        parts.append(f"{facility} 등의 편의시설이 있다.")

    # ── 실내외 여부 ───────────────────────────────────────
    if indoor == "Y" and outdoor == "Y":
        parts.append("실내외 모두 이용 가능하다.")
    elif indoor == "Y":
        parts.append("실내 이용 가능하다.")
    elif outdoor == "Y":
        parts.append("실외 이용 가능하다.")

    # ── 이용 조건 ─────────────────────────────────────────
    if conditions and conditions != "제한사항 없음":
        parts.append(f"{conditions}이 필요하다.")
    if size_hint and size_hint != "모두 가능":
        parts.append(f"{size_hint} 입장 가능하다.")
    if extra_fee and extra_fee != "없음":
        parts.append(f"애견 동반 추가 요금은 {extra_fee}이다.")

    # ── 운영 정보 ─────────────────────────────────────────
    if open_hours:
        parts.append(f"운영시간은 {open_hours}이다.")
    if closed_days:
        parts.append(f"휴무일은 {closed_days}이다.")
    if parking == "Y":
        parts.append("주차 가능하다.")

    return " ".join(parts)


def build_metadata(row: pd.Series) -> dict:
    """ChromaDB 메타데이터 구성 (필터링 및 RDB 조회용)"""

    def safe_str(val, default=""):
        return str(val) if pd.notna(val) else default

    def safe_float(val, default=0.0):
        try:
            return float(val) if pd.notna(val) else default
        except Exception:
            return default

    return {
        "content_id":   safe_str(row.get("content_id")),
        "name":         safe_str(row.get("시설명")),
        "category":     safe_str(row.get("카테고리3")),
        "city":         safe_str(row.get("시도 명칭")),
        "district":     safe_str(row.get("시군구 명칭")),
        "address":      safe_str(row.get("도로명주소")),
        "lat":          safe_float(row.get("위도")),
        "lng":          safe_float(row.get("경도")),
        "indoor":       safe_str(row.get("장소(실내) 여부"), "N"),
        "outdoor":      safe_str(row.get("장소(실외)여부"), "N"),
        "conditions":   safe_str(row.get("반려동물 제한사항")),
        "size_hint":    safe_str(row.get("입장 가능 동물 크기")),
        "open_hours":   safe_str(row.get("운영시간")),
        "closed_days":  safe_str(row.get("휴무일")),
        "parking":      safe_str(row.get("주차 가능여부")),
        "entrance_fee": safe_str(row.get("입장(이용료)가격 정보")),
        "extra_fee":    safe_str(row.get("애견 동반 추가 요금")),
        "tel":          safe_str(row.get("전화번호")),
        "space_size":   safe_str(row.get("공간크기")),
        "vibe":         safe_str(row.get("분위기")),
        "congestion":   safe_str(row.get("혼잡도")),
        "nature":       safe_str(row.get("자연환경")),
        "access":       safe_str(row.get("접근성")),
    }


def main():
    # ── 1. CSV 로드 ──────────────────────────────────────
    print(f"📂 CSV 로딩: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    print(f"   전체 행 수: {len(df)}")

    # 위도/경도 없는 행 제거
    df = df.dropna(subset=["위도", "경도"])
    print(f"   위도/경도 있는 행 수: {len(df)}")

    # ── 2. 임베딩 모델 로드 ──────────────────────────────
    print(f"\n🤖 임베딩 모델 로딩: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)
    print("   모델 로딩 완료!")

    # ── 3. ChromaDB 연결 ─────────────────────────────────
    print(f"\n🗄️  ChromaDB 연결: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # dog_places 컬렉션만 삭제 후 재생성 (다른 컬렉션 유지)
    try:
        client.delete_collection(COLLECTION_NAME)
        print(f"   기존 '{COLLECTION_NAME}' 컬렉션 삭제 완료")
    except Exception:
        print(f"   기존 컬렉션 없음, 새로 생성")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    print(f"   '{COLLECTION_NAME}' 컬렉션 생성 완료")

    # ── 4. 임베딩 텍스트 생성 ────────────────────────────
    print(f"\n📝 임베딩 텍스트 생성 중...")
    texts     = []
    metadatas = []
    ids       = []

    for _, row in df.iterrows():
        text = build_embedding_text(row)
        if not text.strip():
            continue
        texts.append(text)
        metadatas.append(build_metadata(row))
        ids.append(str(uuid.uuid4()))

    print(f"   임베딩 텍스트 생성 완료: {len(texts)}개")

    # 샘플 출력
    print(f"\n📋 샘플 임베딩 텍스트 (첫 3개):")
    for i, text in enumerate(texts[:3]):
        print(f"   [{i+1}] {text[:200]}...")
        print()

    # ── 5. 배치 임베딩 & ChromaDB 적재 ──────────────────
    print(f"\n🚀 ChromaDB 적재 시작 (배치 크기: {BATCH_SIZE})")
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

    print(f"\n✅ 적재 완료! 총 {total}개 장소 임베딩")
    print(f"   저장 위치: {CHROMA_PATH}")

    # ── 6. 검색 테스트 ───────────────────────────────────
    print(f"\n🔍 검색 테스트:")
    test_queries = [
        "한강이랑 비슷한 곳",
        "조용한 공원 강아지 산책",
        "실내 애견카페 넓은 곳",
        "주차 가능한 야외 공원",
        "대중교통으로 가기 좋은 카페",
    ]

    for query in test_queries:
        query_embedding = model.encode(query).tolist()
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3,
        )
        print(f"\n  쿼리: '{query}'")
        for meta, doc in zip(results["metadatas"][0], results["documents"][0]):
            print(f"    → {meta.get('name')} ({meta.get('category')}, {meta.get('city')})")
            print(f"       {doc[:100]}...")


if __name__ == "__main__":
    main()
