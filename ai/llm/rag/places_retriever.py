# ai/llm/rag/places_retriever.py
# 유사 장소 벡터 검색 (dog_places)

from ai.utils.chroma_client import get_collection, COLLECTION_PLACES
from ai.utils.embeddings import embed_text


def search_similar_places(
    query_text: str,
    n_results: int = 5,
    category: str = None,
    city: str = None,
) -> list:
    """
    의미 기반 유사 장소 검색
    → 챗봇 장소 추천 시 RAG 컨텍스트용

    Parameters:
        query_text: 검색 쿼리 (예: "한강이랑 비슷한 넓은 공원")
        n_results: 반환할 장소 수 (기본 5개)
        category: 카테고리 필터 (선택, 예: "카페", "공원", "숙박")
        city: 도시 필터 (선택, 예: "서울특별시", "경기도")

    Returns:
        검색 결과 없으면 빈 리스트 반환
    """
    try:
        collection = get_collection(COLLECTION_PLACES)

        # 필터 구성 — 두 개 동시에 쓸 때 $and 연산자 필요
        if category and city:
            where = {"$and": [{"category": category}, {"city": city}]}
        elif category:
            where = {"category": category}
        elif city:
            where = {"city": city}
        else:
            where = None

        result = collection.query(
            query_embeddings=[embed_text(query_text)],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances"]
        )

        if not result["ids"][0]:
            print(f"장소 검색 결과 없음: '{query_text}'")
            return []

        places = []
        for i in range(len(result["ids"][0])):
            metadata = result["metadatas"][0][i]
            places.append({
                "name": metadata.get("name", ""),
                "address": metadata.get("address", ""),
                "category": metadata.get("category", ""),
                "city": metadata.get("city", ""),
                "lat": metadata.get("lat", 0.0),
                "lng": metadata.get("lng", 0.0),
                "open_hours": metadata.get("open_hours", ""),
                "closed_days": metadata.get("closed_days", ""),
                "parking": metadata.get("parking", ""),
                "entrance_fee": metadata.get("entrance_fee", ""),
                "tel": metadata.get("tel", ""),
                "homepage": metadata.get("homepage", ""),
                "conditions": metadata.get("conditions", ""),
                "size_limit": metadata.get("size_limit", "모두 가능"),
                "indoor": metadata.get("indoor", "N"),
                "outdoor": metadata.get("outdoor", "N"),
                "extra_fee": metadata.get("extra_fee", "없음"),
                "source": metadata.get("source", ""),
                "similarity": round(1 - result["distances"][0][i], 4),
            })

        return places

    except Exception as e:
        print(f"places_retriever 오류: {e}")
        return []


def format_places_context(places: list) -> str:
    """
    장소 목록 → 프롬프트에 넣을 텍스트로 변환
    """
    if not places:
        return ""

    formatted = []
    for place in places:
        name = place.get("name", "")
        category = place.get("category", "")
        city = place.get("city", "")
        address = place.get("address", "")
        open_hours = place.get("open_hours", "")
        closed_days = place.get("closed_days", "")
        parking = place.get("parking", "")
        entrance_fee = place.get("entrance_fee", "")
        tel = place.get("tel", "")
        conditions = place.get("conditions", "")
        size_limit = place.get("size_limit", "")
        indoor = place.get("indoor", "")
        outdoor = place.get("outdoor", "")
        extra_fee = place.get("extra_fee", "")
        homepage = place.get("homepage", "")

        lines = [f"[{name} / {category} / {city}]"]
        lines.append(f"주소: {address}")
        if open_hours:
            lines.append(f"운영시간: {open_hours}")
        if closed_days:
            lines.append(f"휴무일: {closed_days}")
        if parking:
            lines.append(f"주차: {parking}")
        if entrance_fee:
            lines.append(f"입장료: {entrance_fee}")
        if tel:
            lines.append(f"전화번호: {tel}")
        if conditions:
            lines.append(f"이용조건: {conditions}")
        if size_limit and size_limit != "모두 가능":
            lines.append(f"입장 가능 크기: {size_limit}")
        if indoor == "Y" or outdoor == "Y":
            lines.append(f"실내: {indoor} / 실외: {outdoor}")
        if extra_fee and extra_fee != "없음":
            lines.append(f"추가요금: {extra_fee}")
        if homepage:
            lines.append(f"홈페이지: {homepage}")
        
        formatted.append("\n".join(lines))

    return "\n\n".join(formatted)