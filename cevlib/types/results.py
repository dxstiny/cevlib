from __future__ import annotations

import re
from typing import List, Optional

from cevlib.helpers.dictTool import DictEx, ListEx

from cevlib.types.iType import IType, JObject


class SetResult(IType):
    """Result of a single set"""
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
        return self._homeScore

    @property
    def awayScore(self) -> int:
        return self._awayScore

    @property
    def setNumber(self) -> int:
        return self._setNumber

    @property
    def isInPlay(self) -> bool:
        return self._isInPlay

    def __repr__(self) -> str:
        return f"(cevlib.types.results.setResult) {self._homeScore} - {self._awayScore} ({'ongoing' if self._isInPlay else 'finished'})"

    @staticmethod
    def ParseList(setResults: List[JObject]) -> List[SetResult]:
        results = [ ]
        for setResult in setResults:
            result = SetResult(setResult)
            if result:
                results.append(result)
        return results

    @staticmethod
    def ParseFromPlayByPlay(data: JObject) -> SetResult:
        dex = DictEx(data)
        score = ListEx(dex.ensure("Description", str).split("-"))
        return SetResult({
            "homeScore": score.ensure(0, int),
            "awayScore": score.ensure(1, int),
            "setNumber": dex.ensure("SetNumber", int),
            "isInPlay": False
        })


class Result(IType):
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._sets: List[SetResult] = SetResult.ParseList(data.get("setResults") or [ ])
        currentSet = SetResult(dex.ensure("currentSetScore", dict))
        if currentSet:
            self._sets.append(currentSet)
        self._hasGoldenSet: bool = dex.ensure("hasGoldenSet", bool)
        self._homeScore: int = dex.ensure("homeSetsWon", int)
        self._awayScore: int = dex.ensure("awaySetsWon", int)

    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o, Result):
            return False
        return self.toJson() == __o.toJson()

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
    def ParseFromForm(data: JObject) -> Result:
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
    def goldenSet(self) -> Optional[SetResult]:
        if not self.hasGoldenSet:
            return None
        return self.sets[-1]

    @property
    def regularSets(self) -> List[SetResult]:
        if self.hasGoldenSet:
            return self.sets[:-1]
        return self.sets

    @property
    def hasGoldenSet(self) -> bool:
        return self._hasGoldenSet

    @property
    def sets(self) -> List[SetResult]:
        return self._sets

    @property
    def latestSet(self) -> Optional[SetResult]:
        if not len(self.sets):
            return None
        return self.sets[len(self.sets) - 1]

    @property
    def homeScore(self) -> int:
        return self._homeScore

    @property
    def awayScore(self) -> int:
        return self._awayScore

    @property
    def valid(self) -> bool:
        return None not in (self._sets, self._homeScore, self._awayScore)

    def __repr__(self) -> str:
        return f"(cevlib.types.results.Result) {self._homeScore}:{self._awayScore} (Golden Set: {self._hasGoldenSet}) {self._sets}"
