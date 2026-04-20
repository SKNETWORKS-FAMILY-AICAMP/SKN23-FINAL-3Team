# -*- coding: utf-8 -*-
from abc import ABC, abstractmethod


class BaseChain(ABC):

    @abstractmethod
    async def run(self, **kwargs):
        ...