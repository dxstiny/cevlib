# -*- coding: utf-8 -*-
"""cevlib"""
from __future__ import annotations
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from typing import List

from cevlib.helpers.dictTool import DictEx, ListEx

from cevlib.types.iType import IType, JObject
from cevlib.types.results import SetResult
from cevlib.types.types import PlayType


class Play(IType):
    """play/event"""
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._type: PlayType = PlayType.parse(dex.assertGet("Title", str))
        self._currentScore: SetResult = SetResult.parseFromPlayByPlay(data)
        self._playerName: str = dex.assertGet("PlayerName", str).title() # TODO player type
        self._playerNumber: int = dex.assertGet("PlayerNumber", int)
        self._isHome: bool = dex.assertGet("IsHome", bool)

    def toJson(self) -> JObject:
        return {
            "type": self.type.value,
            "currentScore": self.currentScore.toJson(),
            "playerName": self.playerName,
            "playerNumber": self._playerNumber,
            "isHome": self._isHome
        }

    @property
    def valid(self) -> bool:
        return None not in (self._type, self._currentScore, self._playerName)

    @property
    def type(self) -> PlayType:
        """play type (e.g. block, spike, ...)"""
        return self._type

    @property
    def currentScore(self) -> SetResult: # TODO rename to result?
        """current score at time of play"""
        return self._currentScore

    @property
    def playerName(self) -> str:
        """player that performed that play"""
        return self._playerName

    def __repr__(self) -> str:
        return f"(cevlib.types.playByPlay.Play) {self._type} {self._currentScore} by {self._playerName}" # pylint: disable=line-too-long


class Set(IType):
    """play by play set"""
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._plays = [ Play(event) for event in dex.ensure("Events", list) ]
        self._setNumber = ListEx(dex.ensure("TabName", str).split(" ")).ensure(1, int)

    def toJson(self) -> JObject:
        return {
            "plays": [ play.toJson() for play in self.plays ],
            "setNumber": self.setNumber
        }

    @property
    def valid(self) -> bool:
        return bool(self._plays)

    @property
    def plays(self) -> List[Play]:
        """all plays/events"""
        return self._plays

    @property
    def setNumber(self) -> int:
        """set number (1 - 5)"""
        return self._setNumber

    def __repr__(self) -> str:
        return f"(cevlib.types.playByPlay.Set) Set {self._setNumber} {self._plays}"


class PlayByPlay(IType):
    """all plays/events across all sets"""
    def __init__(self, data: JObject) -> None:
        self._sets = [ Set(playEvent)
                       for playEvent in DictEx(data).ensure("PlayEvents", list) ]

    @property
    def valid(self) -> bool:
        return bool(self._sets)

    @property
    def sets(self) -> List[Set]:
        """all sets"""
        return self._sets

    def toJson(self) -> JObject:
        return {
            "sets": [ set_.toJson() for set_ in self.sets ]
        }

    def __repr__(self) -> str:
        return f"(cevlib.types.playByPlay.PlayByPlay) {self._sets}"
