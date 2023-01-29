# -*- coding: utf-8 -*-
"""cevlib"""
from __future__ import annotations
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

# (IMatch can be property or async)
# pylint: disable=invalid-overridden-method

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from pyodide.http import pyfetch

from cevlib.match import Match
from cevlib.helpers.dictTool import DictEx
from cevlib.types.competition import MatchCompetition
from cevlib.types.iMatch import IMatch
from cevlib.types.iType import IType, JObject
from cevlib.types.results import Result
from cevlib.types.team import Team
from cevlib.types.types import MatchState


class CalendarMatch(IMatch):
    """simplified match"""
    def __init__(self,
                 url: Optional[str],
                 competition: MatchCompetition,
                 homeTeam: Team,
                 awayTeam: Team,
                 venue: str,
                 startTime: str,
                 result: Result,
                 finished: bool) -> None:
        self._matchCentreLink = url
        self._competition = competition
        self._homeTeam = homeTeam
        self._awayTeam = awayTeam
        self._venue = venue
        if not startTime.endswith("Z"):
            startTime += "Z"
        self._startTime = datetime.strptime(startTime, "%Y-%m-%dT%H:%M:%SZ")
        duration = (datetime.now() - self._startTime)
        self._finished = True if (self._startTime.year == 1900 or duration.days) else finished
        self._result = result
        self._state = MatchState.parse(datetime.utcnow() >= self._startTime, self._finished)

    @staticmethod
    def parse(data: JObject) -> CalendarMatch:
        """parses from json object"""
        dex = DictEx(data)
        return CalendarMatch(dex.ensureString("MatchCentreUrl"),
                             MatchCompetition({ "Competition": dex.ensureString("CompetitionName"),
                                           "CompetitionLogo": dex.ensureString("CompetitionLogo"),
                                           "Phase": dex.ensureString("PhaseName") }),
                             Team.build( dex.ensureString("HomeTeamName"),
                                         dex.ensureString("HomeTeamLogo"),
                                         dex.ensureString("HomeClubCode"),
                                         True ),
                             Team.build( dex.ensureString("GuestTeamName"),
                                         dex.ensureString("GuestTeamLogo"),
                                         dex.ensureString("GuestClubCode"),
                                         False ),
                             dex.ensureString("StadiumName"),
                             dex.ensureString("MatchDateTime_UTC"),
                             Result({
                                "homeSetsWon": dex.ensureInt("WonSetHome"),
                                "awaySetsWon": dex.ensureInt("WonSetGuest"),
                             }),
                             dex.ensureBool("Finalized"))

    @staticmethod
    def shortcutMatch(competition: MatchCompetition, team: Team) -> CalendarMatch:
        """a match that has only one team. Used in case of direct qualification"""
        return CalendarMatch(None,
                             competition,
                             team,
                             Team.build("", "", "", False),
                             "",
                             datetime.fromtimestamp(0).strftime("%Y-%m-%dT%H:%M:%SZ"),
                             Result({}),
                             True)

    @property
    def teams(self) -> Tuple[Team, Team]:
        """(home, away)"""
        return ( self._homeTeam, self._awayTeam )

    async def toMatch(self) -> Optional[Match]:
        """casts this calendar match to a full match"""
        if not self._matchCentreLink:
            return None
        return await Match.byUrl(self._matchCentreLink)

    def __repr__(self) -> str:
        return f"(cevlib.calendar.CalendarMatch) {self._matchCentreLink} {self._competition} {self._venue} {self._startTime}\n{self._homeTeam}\n{self._awayTeam}\n{self._result}" # pylint: disable=line-too-long

    def toJson(self) -> Dict[str, Any]:
        return {
            "competition": self.competition.toJson(),
            "homeTeam": self.homeTeam.toJson(),
            "awayTeam": self.awayTeam.toJson(),
            "venue": self.venue,
            "startTime": str(self.startTime),
            "result": self.result.toJson(),
            "matchCentreLink": self.matchCentreLink,
            "state": self._state.value
        }

    @property
    def state(self) -> MatchState:
        return self._state

    @property
    def competition(self) -> MatchCompetition:
        return self._competition

    @property
    def homeTeam(self) -> Team:
        return self._homeTeam

    @property
    def awayTeam(self) -> Team:
        return self._awayTeam

    @property
    def venue(self) -> str:
        return self._venue

    @property
    def matchCentreLink(self) -> Optional[str]:
        return self._matchCentreLink

    @property
    def startTime(self) -> datetime:
        return self._startTime

    @property
    def result(self) -> Result:
        return self._result

    @property
    def valid(self) -> bool:
        return True

    @property
    def finished(self) -> bool:
        return self._finished


class Calendar(IType):
    """calendar reader (static methods only)"""
    @staticmethod
    async def matchesOfMonth(month: Optional[int] = None,
                             year: Optional[int] = None) -> List[CalendarMatch]:
        """gets all matches of a month"""
        today = datetime.now()
        timestamp = datetime(year if year else today.year,
                             month if month else today.month, 1).strftime("%Y-%m-%dT%H:%M:%SZ")
        matches: List[Dict[str, Any]] = [ ]
        resp = await pyfetch.get(f"https://www.cev.eu/umbraco/api/CalendarApi/GetCalendar?nodeId=11346&culture=en-US&date={timestamp}") # pylint: disable=line-too-long
        jdata = await resp.json()
        calendar = DictEx(jdata)
        for date in calendar.ensureList("Dates"):
            matches.extend(date.get("Matches") or [ ])
        return [ CalendarMatch.parse(match)
                 for match in matches ]


    @staticmethod
    async def recentMatches() -> List[CalendarMatch]:
        """gets all matches that cev.eu displays as 'recent'"""
        matches = await Calendar._getLiveScoreMatches()
        return [ Calendar._liveScoresToCalendarMatch(match)
                 for match in matches
                 if match.get("matchState_String") == "FINISHED" ]

    @staticmethod
    async def upcomingMatches() -> List[CalendarMatch]:
        """gets all matches that cev.eu displays as 'upcoming'"""
        matches = await Calendar._getLiveScoreMatches()
        return [ Calendar._liveScoresToCalendarMatch(match)
                 for match in matches
                 if not match.get("matchState_String") == "FINISHED" ]

    @staticmethod
    async def upcomingAndRecentMatches() -> List[CalendarMatch]:
        """gets all matches that cev.eu displays as 'recent' or 'upcoming'"""
        matches = await Calendar._getLiveScoreMatches()
        return [ Calendar._liveScoresToCalendarMatch(match)
                 for match in matches ]

    @staticmethod
    def _liveScoresToCalendarMatch(match: Dict[str, Any]) -> CalendarMatch:
        dex = DictEx(match)
        compDict = dex.ensureDict("competition")
        compDict["Phase"] = dex.get("phaseName")
        compDict["Leg"] = dex.get("legName")
        compDict["GroupPool"] = dex.get("groupName")
        compDict["MatchNumber"] = dex.get("matchNumber")
        return CalendarMatch(dex.get("matchCentreLink"),
                             MatchCompetition(compDict),
                             Team.build( dex.ensureString("homeTeam"),
                                         dex.ensureString("homeTeamIcon"),
                                         dex.ensureString("homeTeamNickname"),
                                         True ),
                             Team.build( dex.ensureString("awayTeam"),
                                         dex.ensureString("awayTeamIcon"),
                                         dex.ensureString("awayTeamNickname"),
                                         False ),
                             dex.ensureString("matchLocation"),
                             dex.ensureString("utcStartDate"),
                             Result(match),
                             dex.ensureString("matchState_String") == "FINISHED")

    @staticmethod
    async def _getLiveScoreMatches() -> List[Dict[str, Any]]:
        matches = [ ]
        resp = await pyfetch.get("https://weblivefeed.cev.eu/LiveScores.json")
        jdata = DictEx(await resp.json())
        for competition in jdata.ensure("competitions", list):
            dex = DictEx(competition)
            for match in dex.ensure("matches", list):
                match["competition"] = { "Competition": dex.tryGet("competitionName",
                                                                        str),
                                            "id": dex.tryGet("competitionId", str) }
                matches.append(match)
        return matches

    def __repr__(self) -> str:
        return "(cevlib.calendar.Calendar)"

    def toJson(self) -> Dict[str, Any]:
        return { }

    @property
    def valid(self) -> bool:
        return True
