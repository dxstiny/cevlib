from __future__ import annotations

from enum import Enum
from typing import List
from cevTypes.iType import IType


class TeamStatisticType(Enum):
    WinningSpikes = "winningSpikes"
    KillBlocks = "killBlocks"
    Aces = "aces"
    OpponentErrors = "oppnentErrors"
    Points = "points"
    Unknown = "unknown"

    @staticmethod
    def Parse(value: str) -> TeamStatisticType:
        if value == "Winning Spikes":
            return TeamStatisticType.WinningSpikes
        if value == "Kill Blocks":
            return TeamStatisticType.KillBlocks
        if value == "Aces":
            return TeamStatisticType.Aces
        if value == "Opponent Errors":
            return TeamStatisticType.OpponentErrors
        if value == "Points":
            return TeamStatisticType.Points
        return TeamStatisticType.Unknown


class TeamStatistic(IType):
    def __init__(self, data: dict, home: bool) -> None:
        self._type = TeamStatisticType.Parse(data.get("Name"))
        self._value = data["HomeTeamValue" if home else "AwayTeamValue"]
        self._percent = data["HomeTeamPercent" if home else "AwayTeamPercent"]

    @property
    def valid(self) -> bool:
        return None in (self._type, self._value)

    def __repr__(self) -> str:
        return f"(cevTypes.stats.TeamStatistic) {self._type} {self._value} ({self._percent}%)"


class TeamStatisticSet(IType):
    def __init__(self, data: list, name: str, home: bool) -> None:
        self._stats = [ TeamStatistic(statistic, home) for statistic in data ]
        self._name = name

    @property
    def valid(self) -> bool:
        return self._name is not None

    def byType(self, type_: TeamStatisticType) -> TeamStatistic:
        for stat in self._stats:
            if stat._type == type_:
                return stat

    def __repr__(self) -> str:
        return f"(cevTypes.stats.TeamStatisticSet) {self._name} {self._stats}"


class TeamStatistics(IType):
    def __init__(self, data: dict, home: bool) -> None:
        tabs = data.get("Tabs") or [ ]
        self._setStats: List[TeamStatisticSet] = [ ]
        for tab in tabs:
            self._setStats.append(TeamStatisticSet(tab.get("Statistics"), tab.get("Name"), home))

    @property
    def setStats(self) -> List[TeamStatisticSet]:
        return self._setStats

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevTypes.stats.TeamStatistics) {self._setStats}"


class PlayerStatistic(IType):
    def __init__(self, data: dict) -> None:
        self._points: int = data.get("Points")
        self._serves: int = data.get("Serves")
        self._spikes: int = data.get("Spikes")
        self._blocks: int = data.get("Blocks")
        self._receptions: int = data.get("Reception")
        self._spikePerc: int = int(data.get("SpikePerc").replace("%", ""))
        self._receptionPerc: int = int(data.get("PositiveReceptionPerc").replace("%", ""))

    @property
    def valid(self) -> bool:
        return None in (self._points, self._serves, self._spikes, self._blocks, self._receptions, self._spikePerc, self._receptionPerc)

    @property
    def points(self) -> int:
        assert self.valid
        return self._points

    @property
    def serves(self) -> int:
        assert self.valid
        return self._serves

    @property
    def spikes(self) -> int:
        assert self.valid
        return self._spikes

    @property
    def blocks(self) -> int:
        assert self.valid
        return self._blocks

    @property
    def receptions(self) -> int:
        assert self.valid
        return self._receptions

    @property
    def spikePercentage(self) -> int:
        """0 - 100"""
        assert self.valid
        return self._spikePerc

    @property
    def receptionPercentage(self) -> int:
        """0 - 100"""
        assert self.valid
        return self._receptionPerc

    def __repr__(self) -> str:
        return f"(cevTypes.stats.PlayerStatistic) Spikes: {self._spikes} Blocks: {self._blocks} Points: {self._points} Serves: {self._serves} Receptions: {self._receptions}"
