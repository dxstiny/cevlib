from __future__ import annotations

from enum import Enum

from cevTypes.results import SetResult


class PlayType(Enum):
    Spike = "spike"
    Serve = "serve"
    Block = "block"
    FirstServe = "firstServe"
    Unknown = "unknown"

    @staticmethod
    def Parse(typeName) -> PlayType:
        if typeName == "Spike":
            return PlayType.Spike
        if typeName == "Serve":
            return PlayType.Serve
        if typeName == "Block":
            return PlayType.Block
        if typeName == "First Serve":
            return PlayType.FirstServe
        return PlayType.Unknown


class Play:
    def __init__(self, data: dict) -> None:
        self._type: PlayType = PlayType.Parse(data.get("Title"))
        self._currentScore: SetResult = SetResult.ParseFromPlayByPlay(data)
        self._playerName: str = data.get("PlayerName").title() # TODO player type

    def __repr__(self) -> str:
        return f"(cevTypes.playByPlay.Play) {self._type} {self._currentScore} by {self._playerName}"


class Set:
    def __init__(self, data: dict) -> None:
        self._plays = [ Play(event) for event in data.get("Events") ]
        self._setNumber = int(data.get("TabName").split(" ")[1])

    def __repr__(self) -> str:
        return f"(cevTypes.playByPlay.Set) Set {self._setNumber} {self._plays}"


class PlayByPlay:
    def __init__(self, data: dict) -> None:
        self._sets = [ Set(playEvent) for playEvent in data.get("PlayEvents") ]

    def __repr__(self) -> str:
        return f"(cevTypes.playByPlay.PlayByPlay) {self._sets}"
