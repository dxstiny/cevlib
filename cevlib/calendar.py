from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import aiohttp

from cevlib.match import Match
from cevlib.helpers.dictTool import DictEx
from cevlib.types.competition import Competition
from cevlib.types.iType import IType
from cevlib.types.results import Result
from cevlib.types.team import Team
from cevlib.types.types import MatchState

class CalendarMatch(IType):
    def __init__(self,
                 url: Optional[str],
                 competition: Competition,
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
        self._state = MatchState.Parse(datetime.utcnow() >= self._startTime, self._finished)

    @staticmethod
    def parse(data: Dict[str, Any]) -> CalendarMatch:
        dex = DictEx(data)
        return CalendarMatch(dex.ensureString("MatchCentreUrl"),
                             Competition({ "Competition": dex.ensureString("CompetitionName"),
                                           "CompetitionLogo": dex.ensureString("CompetitionLogo"),
                                           "Phase": dex.ensureString("PhaseName") }),
                             Team.Build( dex.ensureString("HomeTeamName"),
                                         dex.ensureString("HomeTeamLogo"),
                                         dex.ensureString("HomeClubCode"),
                                         True ),
                             Team.Build( dex.ensureString("GuestTeamName"),
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
    def ShortcutMatch(competition: Competition, team: Team) -> CalendarMatch:
        return CalendarMatch(None,
                             competition,
                             team,
                             Team.Build("", "", "", False),
                             "",
                             datetime.fromtimestamp(0).strftime("%Y-%m-%dT%H:%M:%SZ"),
                             Result({}),
                             True)

    @property
    def teams(self) -> Tuple[Team, Team]:
        return ( self._homeTeam, self._awayTeam )

    async def toMatch(self) -> Optional[Match]:
        if not self._matchCentreLink:
            return None
        return await Match.ByUrl(self._matchCentreLink)

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
    def competition(self) -> Competition:
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


class Calendar(IType):
    @staticmethod
    async def MatchesOfMonth(month: Optional[int] = None,
                             year: Optional[int] = None) -> List[CalendarMatch]:
        today = datetime.now()
        timestamp = datetime(year if year else today.year,
                             month if month else today.month, 1).strftime("%Y-%m-%dT%H:%M:%SZ")
        matches: List[Dict[str, Any]] = [ ]
        async with aiohttp.ClientSession() as client:
            async with client.get(f"https://www.cev.eu/umbraco/api/CalendarApi/GetCalendar?nodeId=11346&culture=en-US&date={timestamp}") as resp: # pylint: disable=line-too-long
                jdata = await resp.json(content_type=None)
                calendar = DictEx(jdata)
                for date in calendar.ensureList("Dates"):
                    matches.extend(date.get("Matches") or [ ])
        return [ CalendarMatch.parse(match)
                 for match in matches ]


    @staticmethod
    async def RecentMatches() -> List[CalendarMatch]:
        matches = await Calendar._GetLiveScoreMatches()
        return [ Calendar._LiveScoresToCalendarMatch(match)
                 for match in matches
                 if match.get("matchState_String") == "FINISHED" ]

    @staticmethod
    async def UpcomingMatches() -> List[CalendarMatch]:
        matches = await Calendar._GetLiveScoreMatches()
        return [ Calendar._LiveScoresToCalendarMatch(match)
                 for match in matches
                 if not match.get("matchState_String") == "FINISHED" ]

    @staticmethod
    async def UpcomingAndRecentMatches() -> List[CalendarMatch]:
        matches = await Calendar._GetLiveScoreMatches()
        return [ Calendar._LiveScoresToCalendarMatch(match)
                 for match in matches ]

    @staticmethod
    def _LiveScoresToCalendarMatch(match: Dict[str, Any]) -> CalendarMatch:
        dex = DictEx(match)
        compDict = dex.ensureDict("competition")
        compDict["Phase"] = dex.get("phaseName")
        compDict["Leg"] = dex.get("legName")
        compDict["GroupPool"] = dex.get("groupName")
        compDict["MatchNumber"] = dex.get("matchNumber")
        return CalendarMatch(dex.get("matchCentreLink"),
                             Competition(compDict),
                             Team.Build( dex.ensureString("homeTeam"),
                                         dex.ensureString("homeTeamIcon"),
                                         dex.ensureString("homeTeamNickname"),
                                         True ),
                             Team.Build( dex.ensureString("awayTeam"),
                                         dex.ensureString("awayTeamIcon"),
                                         dex.ensureString("awayTeamNickname"),
                                         False ),
                             dex.ensureString("matchLocation"),
                             dex.ensureString("utcStartDate"),
                             Result(match),
                             dex.ensureString("matchState_String") == "FINISHED")

    @staticmethod
    async def _GetLiveScoreMatches() -> List[Dict[str, Any]]:
        matches = [ ]
        async with aiohttp.ClientSession() as client:
            async with client.get("https://www.cev.eu/LiveScores.json") as resp:
                jdata = await resp.json(content_type=None)
                for competition in jdata.get("competitions"):
                    for m in competition.get("matches"):
                        m["competition"] = { "Competition": competition["competitionName"],
                                             "id": competition["competitionId"] }
                        matches.append(m)

        return matches

    def __repr__(self) -> str:
        return "(cevlib.calendar.Calendar)"

    def toJson(self) -> Dict[str, Any]:
        return { }

    @property
    def valid(self) -> bool:
        return True
