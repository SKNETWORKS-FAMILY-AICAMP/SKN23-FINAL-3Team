# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class BasePromptBuilder(ABC):

    @abstractmethod
    def build_system_prompt(self) -> str:
        ...

    @abstractmethod
    def build_user_prompt(self, **kwargs) -> str:
        ...