import os
import requests

from core.deps import get_db
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from services.place_service import search_places_from_db

router = APIRouter(tags=["places"])

TOUR_API_KEY = os.getenv("TOUR_API_KEY")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
BASE_URL = "https://apis.data.go.kr/B551011/KorPetTourService2"


def get_place_image(place_name: str) -> str:
    """관광공사 API로 이미지 가져오기"""
    try:
        res = requests.get(
            f"{BASE_URL}/searchKeyword2",
            params={
                "serviceKey": TOUR_API_KEY,
                "keyword": place_name,
                "MobileOS": "ETC",
                "MobileApp": "WithDog",
                "_type": "json",
                "numOfRows": 1,
            }
        )
        data = res.json()
        body = data["response"]["body"]
        items = body.get("items")
        if not items or items == "":
            return ""

        item = items["item"]
        item = item[0] if isinstance(item, list) else item
        content_id = item.get("contentid", "")
        if not content_id:
            return ""

        detail_res = requests.get(
            f"{BASE_URL}/detailCommon2",
            params={
                "serviceKey": TOUR_API_KEY,
                "contentId": content_id,
                "defaultYN": "Y",
                "firstImageYN": "Y",
                "MobileOS": "ETC",
                "MobileApp": "WithDog",
                "_type": "json",
            }
        )
        detail_data = detail_res.json()
        detail_items = detail_data["response"]["body"]["items"]
        if not detail_items or detail_items == "":
            return ""
        detail_item = detail_items["item"]
        detail_item = detail_item[0] if isinstance(detail_item, list) else detail_item
        return detail_item.get("firstimage", "")

    except Exception as e:
        print(f"관광공사 API 오류 ({place_name}): {e}")
        return ""


def get_kakao_image(place_name: str) -> str:
    """카카오 이미지 검색으로 fallback"""
    try:
        res = requests.get(
            "https://dapi.kakao.com/v2/search/image",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"},
            params={"query": place_name, "size": 5}
        )
        data = res.json()
        documents = data.get("documents", [])
        # https 이미지만 허용
        for doc in documents:
            url = doc.get("image_url", "")
            if url.startswith("https://"):
                return url
        return ""
    except Exception as e:
        print(f"카카오 이미지 오류 ({place_name}): {e}")
        return ""


@router.get("/search")
async def search_places(query: str, db: AsyncSession = Depends(get_db)):
    places = await search_places_from_db(query, db, n_results=5)
    for place in places:
        image = get_place_image(place["name"])
        if not image:
            image = get_kakao_image(place["name"])
        place["image"] = image
    return {"places": places}