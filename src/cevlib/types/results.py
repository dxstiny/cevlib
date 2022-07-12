# -*- coding: utf-8 -*-
"""cevlib"""
from __future__ import annotations
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

import re
from typing import List, Optional

from cevlib.helpers.dictTool import DictEx, ListEx

from cevlib.types.iType import IType, JArray, JObject


class SetResult(IType):
    """result of a single set"""
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._homeScore: int = dex.ensure("homeScore", int)
        self._awayScore: int = dex.ensure("awayScore", int)
        self._setNumber: int = dex.ensure("setNumber", int)
        self._isInPlay: bool = dex.ensure("isInPlay", bool)

    def toJson(self) -> JObject:
        return {
            "homeScore": self.homeScore,
            "awayScore": self.awayScore,
            "setNumber": self.setNumber,
            "isInPlay": self.isInPlay
        }

    @property
    def valid(self) -> bool:
        return None not in (self._homeScore, self._awayScore, self._setNumber, self._isInPlay)\
            and 0 not in (self._homeScore, self._awayScore)

    @property
    def homeScore(self) -> int:
        """home team score"""
        return self._homeScore

    @property
    def awayScore(self) -> int:
        """away team score"""
        return self._awayScore

    @property
    def setNumber(self) -> int:
        """set number (1 - 5)"""
        return self._setNumber

    @property
    def isInPlay(self) -> bool:
        """is in play?"""
        return self._isInPlay

    def __repr__(self) -> str:
        return f"(cevlib.types.results.setResult) {self._homeScore} - {self._awayScore} ({'ongoing' if self._isInPlay else 'finished'})" # pylint: disable=line-too-long

    @staticmethod
    def parseList(setResults: JArray) -> List[SetResult]:
        """parse result from set results"""
        results = [ ]
        for setResult in setResults:
            result = SetResult(setResult)
            if result:
                results.append(result)
        return results

    @staticmethod
    def parseFromPlayByPlay(data: JObject) -> SetResult:
        """parse result from play by play"""
        dex = DictEx(data)
        score = ListEx(dex.ensure("Description", str).split("-"))
        return SetResult({
            "homeScore": score.ensure(0, int),
            "awayScore": score.ensure(1, int),
            "setNumber": dex.ensure("SetNumber", int),
            "isInPlay": False
        })


class Result(IType):
    """full result"""
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._sets: List[SetResult] = SetResult.parseList(data.get("setResults") or [ ])
        currentSet = SetResult(dex.ensure("currentSetScore", dict))
        if currentSet:
            self._sets.append(currentSet)
        self._hasGoldenSet: bool = dex.ensure("hasGoldenSet", bool)
        self._homeScore: int = dex.ensure("homeSetsWon", int)
        self._awayScore: int = dex.ensure("awaySetsWon", int)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Result):
            return False
        return self.toJson() == other.toJson()

    def toJson(self) -> JObject:
        return {
            "hasGoldenSet": self.hasGoldenSet,
            "sets": [ set_.toJson() for set_ in self.sets ],
            "regularSets": [ set_.toJson() for set_ in self.regularSets ],
            "goldenSet": self.goldenSet.toJson() if self.goldenSet else None,
            "homeScore": self.homeScore,
            "awayScore": self.awayScore
        }

    @staticmethod
    def parseFromForm(data: JObject) -> Result:
        """parses from form match"""
        dex = DictEx(data)
        sets = re.sub(r"[(</span>) ]", "", dex.ensure("SetsFormatted", str)).split(",")
        return Result({
            "homeSetsWon": dex.ensure("HomeTeam", DictEx).ensure("Score", int),
            "awaySetsWon": dex.ensure("AwayTeam", DictEx).ensure("Score", int),
            "setResults": [ {
                "homeScore": ListEx(set.split("-")).ensure(0, int),
                "awayScore": ListEx(set.split("-")).ensure(1, int),
                "setNumber": i + 1,
                "isInPlay": False
            } for (i, set) in enumerate(sets) if not set == "" ]
        })

    @property
    def sets(self) -> List[SetResult]:
        """all sets"""
        return self._sets

    @property
    def regularSets(self) -> List[SetResult]:
        """all regular sets (no golden set)"""
        if self.hasGoldenSet:
            return self.sets[:-1]
        return self.sets

    @property
    def goldenSet(self) -> Optional[SetResult]:
        """golden set (if one exists)"""
        if not self.hasGoldenSet:
            return None
        return self.sets[-1]

    @property
    def hasGoldenSet(self) -> bool:
        """has golden set"""
        return self._hasGoldenSet

    @property
    def latestSet(self) -> Optional[SetResult]:
        """latest set (that might still be active)"""
        if len(self.sets) == 0:
            return None
        return self.sets[len(self.sets) - 1]

    @property
    def homeScore(self) -> int:
        """home team score"""
        return self._homeScore

    @property
    def awayScore(self) -> int:
        """away team score"""
        return self._awayScore

    @property
    def empty(self) -> bool:
        """is empty?"""
        return len(self.sets) == 0 and not self._homeScore and not self._awayScore

    @property
    def valid(self) -> bool:
        return None not in (self._sets, self._homeScore, self._awayScore)

    def __repr__(self) -> str:
        return f"(cevlib.types.results.Result) {self._homeScore}:{self._awayScore} (Golden Set: {self._hasGoldenSet}) {self._sets}" # pylint: disable=line-too-long
