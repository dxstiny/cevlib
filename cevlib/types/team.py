# -*- coding: utf-8 -*-
"""cevlib"""
from __future__ import annotations
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from datetime import datetime
from typing import List, Optional

from cevlib.helpers.dictTool import DictEx, ListEx

from cevlib.types.iType import IType, JArray, JObject
from cevlib.types.matchPoll import TeamPoll
from cevlib.types.stats import PlayerStatistic, TeamStatistics
from cevlib.types.types import Position, Zone
from cevlib.types.results import Result


class Player(IType):
    """player model"""
    def __init__(self, data: JObject, playerStatsData: JArray) -> None:
        dex = DictEx(data)
        self._number = dex.ensure("Number", int)
        self._name = dex.ensure("Name", str, "N/A").title()
        self._position = Position.parse(dex.ensure("Position", str))
        self._image = dex.ensure("Image", str)
        self._isCaptain = dex.ensure("isCaptain", bool)
        self._zone = Zone.parse(dex.ensure("PositionNumber", int))
        self._id = dex.ensure("PlayerId", int)
        self._stats: Optional[PlayerStatistic] = None
        for value in playerStatsData:
            player = DictEx(value)
            if self._name.split(" ")[0] in player.ensure("Name", str).title() and \
               player.ensure("PlayerNumber", int) == self._number:
                self._stats = PlayerStatistic(player)
                break

    @property
    def valid(self) -> bool:
        return self._id is not None

    def toJson(self) -> JObject:
        return {
            "zone": self.zone.value,
            "position": self.position.value,
            "name": self.name,
            "id": self.id,
            "number": self.number,
            "stats": self._stats.toJson() if self._stats else None
        }

    @property
    def zone(self) -> Zone:
        """the player's zone"""
        return self._zone

    @property
    def position(self) -> Position:
        """the player's position"""
        return self._position

    @property
    def name(self) -> str:
        """the player's name"""
        return self._name

    @property
    def id(self) -> int:
        """the player's id"""
        return self._id

    @property
    def number(self) -> int:
        """the player's number"""
        return self._number

    @property
    def stats(self) -> Optional[PlayerStatistic]:
        """the player's stats"""
        return self._stats

    def __repr__(self) -> str:
        return f"(cevlib.types.team.Player) {self._name} ({self._number}/{self._id}) {self._position} ({self._zone})" # pylint: disable=line-too-long


class FormMatch(IType):
    """a very minimal match that is part of a team's 'form'"""
    def __init__(self,
                 won: bool,
                 link: str,
                 homeTeam: Team,
                 awayTeam: Team,
                 result: Result,
                 startTime: datetime) -> None:
        self._won = won
        self._link = link
        self._homeTeam = homeTeam
        self._awayTeam = awayTeam
        self._result = result
        self._startTime = startTime

    def toJson(self) -> JObject:
        return {
            "won": self.won,
            "link": self.link,
            "homeTeam": self._homeTeam.toJson(),
            "awayTeam": self._awayTeam.toJson(),
            "result": self._result.toJson(),
            "startTime": str(self._startTime)
        }

    @property
    def won(self) -> bool:
        """game win"""
        return self._won

    @property
    def link(self) -> str:
        """match centre url"""
        return self._link

    @staticmethod
    def parse(data: JObject) -> List[FormMatch]:
        """parses a form match"""
        matches: List[FormMatch] = [ ]
        for (index, match) in enumerate(data.get("Matches") or [ ]):
            if index >= len(data["RecentForm"]):
                break
            matches.append(FormMatch(data["RecentForm"][index],
                                    match["MatchCentreUrl"],
                                    Team.build(match["HomeTeam"]["Name"],
                                                match["HomeTeam"]["Logo"]["Url"],
                                                "N/A", True),
                                    Team.build(match["AwayTeam"]["Name"],
                                                match["AwayTeam"]["Logo"]["Url"],
                                                "N/A", False),
                                    Result.parseFromForm(match),
                                    datetime.strptime(match["MatchDateTime"], "%Y-%m-%dT%H:%M:%S")))
        return matches

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevlib.types.team.FormMatch) {self._won} ({self._link})"


class Team(IType):
    """team"""
    def __init__(self,
            data: JObject,
            playerStatsData: JObject,
            stats: TeamStatistics,
            matchPollData: JArray,
            form: JObject,
            icon: Optional[str] = None,
            nickname: Optional[str] = None,
            id_: int = 0) -> None:
        dex = DictEx(data)
        pollData = ListEx(matchPollData)
        self._stats = stats
        playerStatsList: JArray = [ ]
        for team in playerStatsData.get("Teams") or [ ]:
            playerStatsList.extend(team.get("Players"))

        teamLogo = dex.ensure("TeamLogo", DictEx)
        self._form = FormMatch.parse(form)
        self._nickname: Optional[str] = nickname
        self._name: Optional[str] = teamLogo.tryGet("AltText", str)
        self._logo: Optional[str] = icon or teamLogo.tryGet("Url", str)
        self._id: Optional[int] = id_ or dex.ensure("TeamId", int)

        self._poll: Optional[TeamPoll] = None
        if len(pollData) == 2:
            team = pollData.ensure(0, DictEx)
            if team.ensure("Id", int) != self._id:
                team = pollData.ensure(1, DictEx)
            self._poll = TeamPoll(team)

        self._players: List[Player] = [ ]
        if "TopLeftPlayer" in data: # assume that the others are as well, might improve
            self._players.append(Player(dex.ensure("TopLeftPlayer", dict), playerStatsList))
            self._players.append(Player(dex.ensure("TopMidPlayer", dict), playerStatsList))
            self._players.append(Player(dex.ensure("TopRightPlayer", dict), playerStatsList))
            self._players.append(Player(dex.ensure("BottomLeftPlayer", dict), playerStatsList))
            self._players.append(Player(dex.ensure("BottomMidPlayer", dict), playerStatsList))
            self._players.append(Player(dex.ensure("BottomRightPlayer", dict), playerStatsList))
            self._players.append(Player(dex.ensure("HeadCoach", dict), playerStatsList))
        self._players.extend([ Player(player, playerStatsList)
                               for player in dex.ensure("FeaturedPlayers", list) ])
        self._players.extend([ Player(player, playerStatsList)
                               for player in dex.ensure("SubPlayers", list) ])

    @staticmethod # TODO (swap with ctor (make parse))
    def build(name: str, icon: str, nickname: str, home: bool, id_: int = 0) -> Team:
        """builds a team"""
        return Team({ "TeamLogo": {
                            "AltText": name,
                            "Url": icon
                        }
                    }, { }, TeamStatistics({ }, home), [ ], { },
                    icon, nickname, id_)

    def toJson(self) -> JObject:
        return {
            "name": self.name,
            "nickname": self.nickname,
            "logo": self.logo,
            "id": self.id,
            "stats": self.stats.toJson(),
            "poll": self.poll.toJson() if self.poll else None,
            "form": [ form.toJson() for form in self.form ],
            "players": [ player.toJson() for player in self.players ]
        }

    @property
    def valid(self) -> bool:
        return None not in (self._name, self._id, self._stats)

    @property
    def form(self) -> List[FormMatch]:
        """the team's form"""
        return self._form

    def __repr__(self) -> str:
        return f"(cevlib.types.team.Team) {self._name} ({self._nickname}/{self._id}) \nplayers={self._players}\nform={self._form}" # pylint: disable=line-too-long

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Team):
            return False
        if self.id and other.id:
            return self.id == other.id
        return self.name == other.name

    @property
    def name(self) -> Optional[str]:
        """the team's name"""
        return self._name

    @property
    def nickname(self) -> Optional[str]:
        """the team's nickname (3 chars)"""
        return self._nickname

    @property
    def logo(self) -> Optional[str]:
        """the team's logo (link)"""
        return self._logo

    @property
    def id(self) -> Optional[int]:
        """the team's id"""
        return self._id

    @property
    def stats(self) -> TeamStatistics:
        """the team's stats"""
        return self._stats

    @property
    def poll(self) -> Optional[TeamPoll]:
        """the team's poll data"""
        return self._poll

    @property
    def players(self) -> List[Player]:
        """the team's players"""
        return self._players

    def getFirstPlayer(self,
                  zone: Optional[Zone] = None,
                  position: Optional[Position] = None,
                  id_: Optional[int] = None,
                  number: Optional[int] = None) -> Optional[Player]:
        """the team's first player that matches the filters"""
        players = self.getPlayers(zone, position, id_, number)
        if len(players) > 0:
            return players[0]
        return None

    def getPlayers(self,
                  zone: Optional[Zone] = None,
                  position: Optional[Position] = None,
                  id_: Optional[int] = None,
                  number: Optional[int] = None) -> List[Player]:
        """the team's filtered players"""
        eligiblePlayers = self._players
        if zone:
            eligiblePlayers = [ player
                                for player in eligiblePlayers
                                if player.zone == zone ]
        if position:
            eligiblePlayers = [ player
                                for player in eligiblePlayers
                                if player.position == position ]
        if id_ is not None:
            eligiblePlayers = [ player
                                for player in eligiblePlayers
                                if player.id == id_ ]
        if number is not None:
            eligiblePlayers = [ player
                                for player in eligiblePlayers
                                if player.number == number ]
        return eligiblePlayers
