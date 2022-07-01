# -*- coding: utf-8 -*-
"""cevlib"""
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from cevlib.helpers.dictTool import DictEx
from cevlib.types.iType import IType, JObject


class TeamPoll(IType):
    """team poll (who will win?)"""
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._percent: float = dex.ensure("Percent", float)
        self._count: int = dex.ensure("VoteCount", int)

    def toJson(self) -> JObject:
        return {
            "percent": self.percent,
            "count": self.count
        }

    def __repr__(self) -> str:
        return f"(cevlib.types.matchPoll.TeamPoll) {self._count} ({self._percent})"

    @property
    def percent(self) -> float:
        """percentage that voted for this team (0 - 100)"""
        return self._percent

    @property
    def count(self) -> int:
        """number of votes"""
        return self._count

    @property
    def valid(self) -> bool:
        return None not in (self._percent, self._count)
