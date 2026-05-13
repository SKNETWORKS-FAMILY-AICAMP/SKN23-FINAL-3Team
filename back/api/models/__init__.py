# -*- coding: utf-8 -*-
"""
models/__init__.py
------------------
모든 ORM 모델을 이 패키지에서 임포트합니다.

`init_db()` 에서 `import models` 를 호출하면 이 파일이 실행되어
모든 모델 클래스가 Base.metadata에 등록됩니다.
새 모델 파일을 추가할 때 반드시 이 파일에도 임포트를 추가해주세요.
"""

from models.image import Image
from models.keyword import Keyword
from models.breed import Breed
from models.user import User
from models.pet import Pet
from models.chat_room import ChatRoom
from models.chat_message import ChatMessage
from models.diary import Diary
from models.place import Place
from models.favorite_place import FavoritePlace
from models.pet_profile import PetProfile

__all__ = [
    "Image",
    "Keyword",
    "Breed",
    "User",
    "Pet",
    "PetProfile",
    "ChatRoom",
    "ChatMessage",
    "Diary",
    "Place",
    "FavoritePlace",
]
