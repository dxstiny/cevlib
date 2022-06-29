# -*- coding: utf-8 -*-
"""cevlib"""
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from abc import ABC, abstractmethod
from typing import Any, Coroutine, Dict, List, Union


JObject = Dict[str, Any]
JArray = List[Dict[str, Any]]

class IType(ABC):
    """model interface"""
    @property
    @abstractmethod
    def valid(self) -> bool:
        """is valid?"""

    def __bool__(self) -> bool:
        return self.valid

    @abstractmethod
    def toJson(self) -> Union[JObject,
                          JArray,
                          List[JArray],
                          Coroutine[Any, Any, JObject],
                          Coroutine[Any, Any, JArray]]:
        """serialise"""
