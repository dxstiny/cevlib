from __future__ import annotations
from typing import List, Optional

from cevlib.helpers.dictTool import DictEx

from cevlib.types.iType import IType, JArray, JObject
from cevlib.types.types import Position, TeamStatisticType, TopPlayerType


class TeamStatistic(IType):
    def __init__(self, data: JObject, home: bool) -> None:
        dex = DictEx(data)
        self._type = TeamStatisticType.Parse(dex.ensure("Name", str))
        self._value = dex.ensure("HomeTeamValue" if home else "AwayTeamValue", str) # TODO find out type (str, int)
        self._percent = dex.ensure("HomeTeamPercent" if home else "AwayTeamPercent", str)

    def toJson(self) -> JObject:
        return {
            "type": self.type.value,
            "value": self._value,
            "percent": self._percent
        }

    @property
    def type(self) -> TeamStatisticType:
        return self._type

    @property
    def value(self) -> str:
        return self._value

    @property
    def percent(self) -> str:
        return self._percent

    @property
    def valid(self) -> bool:
        return None not in (self._type, self._value)

    def __repr__(self) -> str:
        return f"(cevlib.types.stats.TeamStatistic) {self._type} {self._value} ({self._percent}%)"


class TeamStatisticSet(IType):
    def __init__(self, data: JArray, name: str, home: bool) -> None:
        self._stats = [ TeamStatistic(statistic, home) for statistic in data ]
        self._name = name

    def toJson(self) -> JObject:
        return {
            "stats": [ stat.toJson() for stat in self.stats ],
            "name": self.name
        }

    @property
    def valid(self) -> bool:
        return self._name is not None

    @property
    def stats(self) -> List[TeamStatistic]:
        return self._stats

    @property
    def name(self) -> str:
        return self._name

    def byType(self, type_: TeamStatisticType) -> Optional[TeamStatistic]:
        for stat in self._stats:
            if stat._type == type_:
                return stat
        return None

    def __repr__(self) -> str:
        return f"(cevlib.types.stats.TeamStatisticSet) {self._name} {self._stats}"


class TeamStatistics(IType):
    def __init__(self, data: JObject, home: bool) -> None:
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
        return f"(cevlib.types.stats.TeamStatistics) {self._setStats}"

    def toJson(self) -> JObject:
        return {
            "setStats": [ setStat.toJson() for setStat in self._setStats ]
        }


class PlayerStatistic(IType):
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._points: int = dex.ensure("Points", int)
        self._serves: int = dex.ensure("Serves", int)
        self._spikes: int = dex.ensure("Spikes", int)
        self._blocks: int = dex.ensure("Blocks", int)
        self._receptions: int = dex.ensure("Reception", int)
        self._spikePerc: int = int(dex.ensure("SpikePerc", str).replace("%", ""))
        self._receptionPerc: int = int(dex.ensure("PositiveReceptionPerc", str).replace("%", ""))

    @property
    def valid(self) -> bool:
        return None not in (self._points, self._serves, self._spikes, self._blocks, self._receptions, self._spikePerc, self._receptionPerc)

    def toJson(self) -> JObject:
        return {
            "points": self.points,
            "serves": self.serves,
            "spikes": self.spikes,
            "blocks": self.blocks,
            "receptions": self.receptions,
            "spikePercentage": self.spikePercentage,
            "receptionPercentage": self.receptionPercentage
        }

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
        return f"(cevlib.types.stats.PlayerStatistic) Spikes: {self._spikes} Blocks: {self._blocks} Points: {self._points} Serves: {self._serves} Receptions: {self._receptions}"


class TopPlayerPlayer(IType):
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._number: int = dex.ensure("Number", int)
        self._name: str = dex.ensure("Name", str)
        self._position = Position.Parse(dex.ensure("Position", str))
        self._score: int = dex.ensure("Score", int)
        self._nationality: str = dex.ensure("Team", str)
        self._image: str = dex.ensure("Image", str)

    def toJson(self) -> JObject:
        return {
            "number": self.number,
            "name": self.name,
            "position": self.position.value,
            "score": self.score,
            "nationality": self.nationality,
            "image": self.image
        }

    @property
    def valid(self) -> bool:
        return None not in (self._number, self._name, self._position, self._score)

    @property
    def number(self) -> int:
        return self._number

    @property
    def score(self) -> int:
        return self._score

    @property
    def position(self) -> Position:
        return self._position

    @property
    def name(self) -> str:
        return self._name

    @property
    def nationality(self) -> str:
        return self._nationality

    @property
    def image(self) -> str:
        return self._image

    def __repr__(self) -> str:
        return f"(cevlib.types.stats.TopPlayerPlayer) {self._name} ({self._number}) Score: {self._score} as {self._position}"


class TopPlayer(IType):
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._type = TopPlayerType.Parse(dex.ensure("Type", str))
        self._players: List[TopPlayerPlayer] = [ ]
        for player in dex.ensure("Match", DictEx).ensure("Players", list):
            self._players.append(TopPlayerPlayer(player))

    def toJson(self) -> JObject:
        return {
            "type": self._type.value,
            "players": [ player.toJson() for player in self._players ]
        }

    @property
    def valid(self) -> bool:
        return bool(self._players)

    @property
    def type(self) -> TopPlayerType:
        return self._type

    @property
    def players(self) -> List[TopPlayerPlayer]:
        return self._players

    @property
    def topPlayer(self) -> TopPlayerPlayer:
        return self._players[0]

    def __repr__(self) -> str:
        return f"(cevlib.types.stats.TopPlayer) {self._type} {self._players}"


class TopPlayers(IType):
    def __init__(self) -> None:
        self._topPlayers: List[TopPlayer] = [ ]

    def toJson(self) -> JObject:
        return {
            "topPlayers": [ player.toJson() for player in self._topPlayers ]
        }

    def topPlayers(self) -> List[TopPlayer]:
        return self._topPlayers

    def append(self, topPlayer: TopPlayer) -> None:
        for player in self._topPlayers:
            if player.type == topPlayer.type:
                return
        self._topPlayers.append(topPlayer)

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevlib.types.stats.TopPlayers) {self._topPlayers}"
