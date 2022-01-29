from __future__ import annotations
from enum import Enum
from typing import List, Optional
from cevTypes.iType import IType
from cevTypes.stats import PlayerStatistic, TeamStatistics


class PlayerPosition(Enum):
    Setter = "setter"
    MiddleBlocker = "middleBlocker"
    OutsideSpiker = "outsideSpiker"
    Opposite = "opposite"
    Libero = "libero"
    HeadCoach = "headCoach"
    Unknown = "unknown"

    @staticmethod
    def Parse(value: str) -> PlayerPosition:
        if value == "Setter":
            return PlayerPosition.Setter
        if value == "Middle blocker":
            return PlayerPosition.MiddleBlocker
        if value == "Outside spiker":
            return PlayerPosition.OutsideSpiker
        if value == "Opposite":
            return PlayerPosition.Opposite
        if value == "Libero":
            return PlayerPosition.Libero
        if value == "Head Coach":
            return PlayerPosition.HeadCoach
        return PlayerPosition.Unknown


class Zone(Enum):
    One = 1
    Two = 2
    Three = 3
    Four = 4
    Five = 5
    Six = 6
    Sub = 0
    Featured = 7
    Unknown = -1

    @staticmethod
    def Parse(value: int) -> Zone:
        if value == 1:
            return Zone.One
        if value == 2:
            return Zone.Two
        if value == 3:
            return Zone.Three
        if value == 4:
            return Zone.Four
        if value == 5:
            return Zone.Five
        if value == 6:
            return Zone.Six
        if value in (7, 8):
            return Zone.Featured
        if value == 0:
            return Zone.Sub
        return Zone.Unknown


class Player(IType):
    def __init__(self, data: dict, playerStatsData: list) -> None:
        self._number = data.get("Number")
        self._name = data.get("Name").title()
        self._position = PlayerPosition.Parse(data.get("Position"))
        self._image = data.get("Image")
        self._isCaptain = data.get("isCaptain") or False
        self._zone = Zone.Parse(data.get("PositionNumber"))
        self._id = data.get("PlayerId")
        self._stats: Optional[PlayerStatistic] = None
        for player in playerStatsData:
            if self._name.split(" ")[0] in player.get("Name").title() and player.get("PlayerNumber") == self._number:
                self._stats = PlayerStatistic(player)
                break

    @property
    def valid(self) -> bool:
        return self._id is not None

    @property
    def zone(self) -> Zone:
        return self._zone
    
    @property
    def position(self) -> PlayerPosition:
        return self._position

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> int:
        return self._id
    
    @property
    def number(self) -> int:
        return self._number

    @property
    def stats(self) -> PlayerStatistic:
        return self._stats

    def __repr__(self) -> str:
        return f"(cevTypes.team.Player) {self._name} ({self._number}/{self._id}) {self._position} ({self._zone})"


class Team(IType):
    def __init__(self, data: dict, playerStatsData: dict, stats: TeamStatistics) -> None:
        self._stats = stats
        playerStatsList: List[PlayerStatistic] = [ ]
        for team in playerStatsData.get("Teams"):
            playerStatsList.extend(team.get("Players"))

        teamLogo = data.get("TeamLogo") or { }
        self._name = teamLogo.get("AltText")
        self._logo = teamLogo.get("Url")
        self._id = data.get("TeamId")
        self._players: List[Player] = [ ]
        self._players.append(Player(data.get("TopLeftPlayer"), playerStatsList))
        self._players.append(Player(data.get("TopMidPlayer"), playerStatsList))
        self._players.append(Player(data.get("TopRightPlayer"), playerStatsList))
        self._players.append(Player(data.get("BottomLeftPlayer"), playerStatsList))
        self._players.append(Player(data.get("BottomMidPlayer"), playerStatsList))
        self._players.append(Player(data.get("BottomRightPlayer"), playerStatsList))
        self._players.append(Player(data.get("HeadCoach"), playerStatsList))
        self._players.extend([ Player(player, playerStatsList) for player in data.get("FeaturedPlayers") or [ ] ])
        self._players.extend([ Player(player, playerStatsList) for player in data.get("SubPlayers") or [ ] ])

    @property
    def valid(self) -> bool:
        return None not in (self._name, self._id, self._stats)

    def __repr__(self) -> str:
        return f"(cevTypes.team.Team) {self._name} ({self._id}) {self._players}"

    @property
    def stats(self) -> TeamStatistics:
        return self._stats

    def getFirstPlayer(self,
                  zone: Optional[Zone] = None,
                  position: Optional[PlayerPosition] = None,
                  id_: Optional[int] = None,
                  number: Optional[int] = None) -> Optional[Player]:
        players = self.getPlayers(zone, position, id_, number)
        if len(players):
            return players[0]
        return None

    def getPlayers(self,
                  zone: Optional[Zone] = None,
                  position: Optional[PlayerPosition] = None,
                  id_: Optional[int] = None,
                  number: Optional[int] = None) -> List[Player]:
        eligiblePlayers = self._players
        if zone:
            eligiblePlayers = [ player for player in eligiblePlayers if player.zone == zone ]
        if position:
            eligiblePlayers = [ player for player in eligiblePlayers if player.position == position ]
        if id_ is not None:
            eligiblePlayers = [ player for player in eligiblePlayers if player.id == id_ ]
        if number is not None:
            eligiblePlayers = [ player for player in eligiblePlayers if player.number == number ]
        return eligiblePlayers
