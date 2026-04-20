import random

dummy_place = [
    {
        "name": "서울숲",
        "address": "서울특별시 성동구 성수동1가 685",
        "type": "공원",
        "description": "반려견 동반 가능",
        "latitude": 37.543066,
        "longitude": 127.041944,
    },
    {
        "name": "올림픽공원",
        "address": "서울특별시 송파구 올림픽로 424",
        "type": "공원",
        "description": "반려견 동반 가능",
        "latitude": 37.520000,
        "longitude": 127.120000,
    },
    {
        "name": "월드컵공원",
        "address": "서울특별시 마포구 하늘공원로 95",
        "type": "공원",
        "description": "반려견 동반 가능",
        "latitude": 37.570000,
        "longitude": 126.870000,
    },
    {
        "name": "선유도공원",
        "address": "서울특별시 영등포구 선유로 343",
        "type": "공원",
        "description": "반려견 동반 가능",
        "latitude": 37.530000,
        "longitude": 126.890000,
    },
    {
        "name": "보라매공원",
        "address": "서울특별시 동작구 여의대방로20길 33",
        "type": "공원",
        "description": "반려견 동반 가능",
        "latitude": 37.490000,
        "longitude": 126.920000,
    },
]


class Place():

    def __init__():
        pass

    async def find_place():
        return random.choice(dummy_place)