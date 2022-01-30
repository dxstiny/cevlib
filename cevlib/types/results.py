from __future__ import annotations

from typing import List, Optional

from cevlib.types.iType import IType


class SetResult(IType):
    """Result of a single set"""
    def __init__(self, data: dict) -> None:
        self._homeScore: Optional[int] = data.get("homeScore")
        self._awayScore: Optional[int] = data.get("awayScore")
        self._setNumber: Optional[int] = data.get("setNumber")
        self._isInPlay: Optional[bool] = data.get("isInPlay")

    @property
    def valid(self) -> bool:
        return None not in (self._homeScore, self._awayScore, self._setNumber, self._isInPlay) \
            and 0 not in (self._homeScore, self._awayScore)

    @property
    def homeScore(self) -> int:
        assert self
        return self._homeScore

    @property
    def awayScore(self) -> int:
        assert self
        return self._awayScore

    @property
    def setNumber(self) -> int:
        assert self
        return self._setNumber

    @property
    def isInPlay(self) -> bool:
        assert self
        return self._isInPlay

    def __repr__(self) -> str:
        return f"(cevlib.types.results.setResult) {self._homeScore} - {self._awayScore} ({'ongoing' if self._isInPlay else 'finished'})"

    @staticmethod
    def ParseList(setResults: List[dict]) -> List[SetResult]:
        results = [ ]
        for setResult in setResults:
            result = SetResult(setResult)
            if result:
                results.append(result)
        return results

    @staticmethod
    def ParseFromPlayByPlay(data: dict) -> SetResult:
        score = data["Description"]
        return SetResult({
            "homeScore": int(score.split("-")[0]),
            "awayScore": int(score.split("-")[1]),
            "setNumber": int(data["SetNumber"]),
            "isInPlay": False
        })


class Result(IType):
    def __init__(self, data: dict) -> None:
        self._sets: List[SetResult] = SetResult.ParseList(data.get("setResults") or [ ])
        currentSet = SetResult(data.get("currentSetScore"))
        if currentSet:
            self._sets.append(currentSet)
        self._goldenSet: Optional[SetResult] = data.get("hasGoldenSet") # TODO (wait for some match to include a golden set :) )
        self._homeScore: Optional[int] = data.get("homeSetsWon") or 0
        self._awayScore: Optional[int] = data.get("awaySetsWon") or 0

    @property
    def valid(self) -> bool:
        return None not in (self._sets, self._homeScore, self._awayScore)

    def __repr__(self) -> str:
        return f"(cevlib.types.results.Result) {self._homeScore}:{self._awayScore} (Golden Set: {self._goldenSet}) {self._sets}"
