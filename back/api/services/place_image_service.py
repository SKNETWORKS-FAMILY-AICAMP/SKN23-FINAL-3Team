"""Place image enrichment helpers shared by chat and REST place search."""

from __future__ import annotations

import asyncio
import logging
import os

import requests

logger = logging.getLogger(__name__)

TOUR_API_KEY = os.getenv("TOUR_API_KEY")
KAKAO_REST_API_KEY = os.getenv("KAKAO_REST_API_KEY")
BASE_URL = "https://apis.data.go.kr/B551011/KorPetTourService2"
REQUEST_TIMEOUT = 3


def _get_place_image_sync(content_id: str) -> str:
    """Fetch a place image from the Korea Tourism Organization API."""
    if not content_id:
        return ""

    try:
        res = requests.get(
            f"{BASE_URL}/detailImage2",
            params={
                "serviceKey": TOUR_API_KEY,
                "contentId": content_id,
                "imageYN": "Y",
                "subImageYN": "Y",
                "MobileOS": "ETC",
                "MobileApp": "WithDog",
                "_type": "json",
            },
            timeout=REQUEST_TIMEOUT,
        )
        data = res.json()
        items = data["response"]["body"].get("items")

        if not items or items == "":
            return ""

        item = items["item"]
        item = item[0] if isinstance(item, list) else item
        return item.get("originimgurl", "")
    except Exception as e:
        logger.info("TourAPI place image lookup failed | content_id=%s | error=%s", content_id, e)
        return ""


def _get_kakao_image_sync(place_name: str) -> str:
    """Fetch a fallback place image from Kakao image search."""
    if not place_name:
        return ""

    try:
        res = requests.get(
            "https://dapi.kakao.com/v2/search/image",
            headers={"Authorization": f"KakaoAK {KAKAO_REST_API_KEY}"},
            params={"query": place_name, "size": 5},
            timeout=REQUEST_TIMEOUT,
        )
        data = res.json()
        for doc in data.get("documents", []):
            url = doc.get("image_url", "")
            if url.startswith("https://"):
                return url
        return ""
    except Exception as e:
        logger.info("Kakao image lookup failed | place=%s | error=%s", place_name, e)
        return ""


async def enrich_place_images(places: list[dict]) -> list[dict]:
    """Attach image URLs to place dictionaries in-place and return them."""
    for place in places:
        image = await asyncio.to_thread(_get_place_image_sync, place.get("content_id", ""))
        if not image:
            image = await asyncio.to_thread(_get_kakao_image_sync, place.get("name", ""))
        place["image"] = image
    return places
