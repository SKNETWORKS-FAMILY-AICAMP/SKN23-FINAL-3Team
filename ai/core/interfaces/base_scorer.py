# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class BaseScorer(ABC):

    @abstractmethod
    def calculate_vector(self, tags: list[str]) -> dict[str, float]:
        ...

    @abstractmethod
    def classify_type(self, tags: list[str]) -> str:
        ...