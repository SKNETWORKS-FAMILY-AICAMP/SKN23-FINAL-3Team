# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class BaseRetriever(ABC):

    @abstractmethod
    def search(self, query: str, **kwargs) -> list[dict]:
        ...

    @abstractmethod
    def format_context(self, results: list[dict]) -> str:
        ...