from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
from time import time
from typing import Coroutine, List, Optional
from pyodide.http import pyfetch
import re
import json
from cevlib_exceptions import NotInitialisedException
from cevlib_helpers_asyncThread import asyncRunInThreadWithReturn
from cevlib_types_competition import Competition
from cevlib_types_iType import IType
from cevlib_types_info import Info

from cevlib_types_playByPlay import PlayByPlay
from cevlib_types_report import MatchReport
from cevlib_types_results import Result
from cevlib_types_stats import TeamStatistics, TopPlayer, TopPlayers
from cevlib_types_team import Team
from cevlib_converters_scoreHeroToJson import ScoreHeroToJson
from cevlib_types_types import MatchState


class MatchCache(IType):
    def __init__(self,
                 playByPlay: Optional[PlayByPlay],
                 competition: Optional[Competition],
                 topPlayers: TopPlayers,
                 gallery: List[str],
                 matchCentreLink: str,
                 currentScore: Result,
                 duration: timedelta,
                 startTime: datetime,
                 venue: str,
                 homeTeam: Team,
                 awayTeam: Team,
                 watchLink: str,
                 highlightsLink: str,
                 state: MatchState,
                 report: Optional[MatchReport],
                 info: Optional[Info]) -> None:
        self._playByPlay = playByPlay
        self._competition = competition
        self._topPlayers = topPlayers
        self._gallery = gallery
        self._matchCentreLink = matchCentreLink
        self._currentScore = currentScore
        self._duration = duration
        self._startTime = startTime
        self._homeTeam = homeTeam
        self._awayTeam = awayTeam
        self._venue = venue
        self._watchLink = watchLink
        self._highlightsLink = highlightsLink
        self._state = state
        self._report = report
        self._info = info

    def toJson(self) -> dict:
        return {
            "state": self.state.value,
            "currentScore": self.currentScore.toJson(),
            "homeTeam": self.homeTeam.toJson(),
            "awayTeam": self.awayTeam.toJson(),
            "competition": self.competition.toJson() if self.competition else None,
            "duration": str(self.duration),
            "startTime": str(self.startTime),
            "matchCentreLink": self.matchCentreLink,
            "watchLink": self.watchLink,
            "highlightsLink": self.highlightsLink,
            "venue": self.venue,
            "report": self.report.toJson() if self.report else None,
            "info": self._info.toJson() if self._info else None,
            "topPlayers": self.topPlayers.toJson(),
            "gallery": self.gallery,
            "playByPlay": self.playByPlay.toJson() if self.playByPlay else None,
        }

    @property
    def valid(self) -> bool:
        return True

    @property
    def playByPlay(self) -> PlayByPlay:
        return self._playByPlay

    @property
    def competition(self) -> Optional[Competition]:
        return self._competition

    @property
    def topPlayers(self) -> TopPlayers:
        return self._topPlayers

    @property
    def gallery(self) -> List[str]:
        return self._gallery

    @property
    def matchCentreLink(self) -> str:
        return self._matchCentreLink

    @property
    def currentScore(self) -> Result:
        return self._currentScore

    @property
    def duration(self) -> timedelta:
        return self._duration

    @property
    def startTime(self) -> datetime:
        return self._startTime

    @property
    def venue(self) -> str:
        return self._venue

    @property
    def homeTeam(self) -> Team:
        return self._homeTeam

    @property
    def awayTeam(self) -> Team:
        return self._awayTeam

    @property
    def watchLink(self) -> str:
        return self._watchLink

    @property
    def highlightsLink(self) -> str:
        return self._highlightsLink

    @property
    def state(self) -> MatchState:
        return self._state

    @property
    def report(self) -> MatchReport:
        return self._report

    @staticmethod
    async def FromMatch(match: Match) -> MatchCache:
        return await match.cache()

    def __repr__(self) -> str:
        return f"(cevlib.match.MatchCache) {self.toJson()}"


class Match(IType):
    def __init__(self, html: str, url: str) -> None:
        self._invalidMatchCentre = "This page can be replaced with a custom 404. Check the documentation for" in html or "Object reference not set to an instance of an object." in html
        #if self._invalidMatchCentre:
            #raise AttributeError("404")
        self._umbracoLinks = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*umbraco[\w.,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        self._gallery = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*Upload\/Photo\/[\w .,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-]).(jpg|JPG)", html) ]
        embeddedVideos = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*\/embed\/[\w .,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        self._highlightsLinkCache: Optional[str] = None
        if len(embeddedVideos):
            self._highlightsLinkCache = "https://" + embeddedVideos[0].replace("/embed/", "/v/").split("?")[0]
        self._nodeId = self._getParameter(self._getLink("livescorehero"), "nodeId")
        self._html = html
        self._matchId: Optional[int] = None
        self._liveScoresCache: Optional[dict] = None
        self._formCache: Optional[dict] = None
        self._finished = False
        self._matchCentreLink = url
        self._initialised = False
        self._reportCache: Optional[MatchReport] = None
        self._infoCache: Optional[Info] = None
        self._scoreObservers: List[Coroutine] = [ ]
        self._scoreObserverInterval = 20
        self._init = asyncio.create_task(self._startInit())
        asyncio.create_task(self._observeScore())

    @property
    def valid(self) -> bool:
        return len(self._umbracoLinks) and self._matchCentreLink is not None

    async def _startInit(self) -> None:
        self._matchId = await self._getMatchId()
        self._initialised = True

    def init(self) -> asyncio.Task:
        """
        caches the match id, required for:
        - homeTeam/awayTeam
        - currentScore
        - startTime
        - duration
        - finished
        - venue
        - watchLink
        - highlightsLink
        """
        return self._init


    # HELPERS


    def _getParameter(self, link: str, parameter: str) -> Optional[str]:
        try:
            return re.search(f"(?<={parameter}=)([A-Za-z0-9]*)(?=&)?", link)[0]
        except:
            return None

    def _getLinks(self, contains: str) -> str:
        eligibleLinks = [ ]
        for umbracoLink in self._umbracoLinks:
            if contains in umbracoLink:
                eligibleLinks.append("https://" + umbracoLink.replace("amp;", ""))
        return eligibleLinks

    def _getLink(self, contains: str, index: int = 0) -> Optional[str]:
        links = self._getLinks(contains)
        if len(links) > index:
            return links[index]
        return None

    async def _getForm(self) -> dict:
        if not self._formCache:
            resp = await pyfetch(self._getLink("GetFormComponent"))
            self._formCache = json.loads(await resp.json())
        return self._formCache

    async def _getMatchId(self) -> int:
        try:
            resp = await pyfetch(self._getLink("livescorehero"))
            jdata = await resp.json()
            return int(jdata.get("MatchId"))
        except:
            return None

    async def _requestLiveScoresJson(self, useCache = True) -> dict:
        if useCache and self._liveScoresCache:
            return self._liveScoresCache
        resp = await pyfetch("https://www.cev.eu/LiveScores.json")
        jdata = await resp.json()
        self._liveScoresCache = jdata
        return jdata

    async def _requestLiveScoresJsonByMatchSafe(self, useCache = True) ->  Optional[dict]:
        return await (self._requestLiveScoresJsonByMatchId(useCache) if not self._invalidMatchCentre else self._requestLiveScoresJsonByMatchCentreLink(useCache))

    async def _requestLiveScoresJsonByMatchCentreLink(self, useCache = True) -> Optional[dict]:
        assert self._matchCentreLink
        jdata = await self._requestLiveScoresJson(useCache)
        for competition in jdata["competitions"]:
            for match in competition["matches"]:
                if match["matchCentreLink"] == self._matchCentreLink:
                    self._finished = match.get("matchState_String") == "FINISHED"
                    match["competition"] = { "name": competition["competitionName"], "id": competition["competitionId"] }
                    return match
        return await self._tryGetFinishedGameData()

    async def _requestLiveScoresJsonByMatchId(self, useCache = True) -> Optional[dict]:
        assert self._matchId
        jdata = await self._requestLiveScoresJson(useCache)
        for competition in jdata["competitions"]:
            for match in competition["matches"]:
                if match["matchId"] == self._matchId:
                    self._finished = match.get("matchState_String") == "FINISHED"
                    return match
        return await self._tryGetFinishedGameData()

    async def _tryGetFinishedGameData(self, trulyFinished = True) -> Optional[dict]:
        if self._invalidMatchCentre:
            return None
        self._finished = trulyFinished
        livescorehero = { }
        matchpolldata = [ ]
        resp = await pyfetch(self._getLink("getlivescorehero"))
        livescorehero = await resp.json()
        resp = await pyfetch(self._getLink("GetMatchPoll"))
        matchpolldata = await resp.json()
        return ScoreHeroToJson.convert(livescorehero, matchpolldata)

    async def _getTeam(self, index: int, home: bool) -> Optional[Team]:
        try:
            playerStatsData = { }
            teamData = { }
            teamStatsData = { }
            matchPoll = [ ]
            resp = await pyfetch(self._getLink("GetStartingTeamComponent", index))
            teamData = await resp.json()
            resp = await pyfetch(self._getLink("GetPlayerStatsComponentMC"))
            playerStatsData = json.loads(await resp.json())
            resp = await pyfetch(self._getLink("GetTeamStatsComponentMC"))
            teamStatsData = json.loads(await resp.json())
            resp = await pyfetch(self._getLink("GetMatchPoll"))
            matchPoll = await resp.json()
            liveScore = await self._requestLiveScoresJsonByMatchSafe()
            form = await self._getForm()
            return Team(teamData, playerStatsData, TeamStatistics(teamStatsData, home), matchPoll,
                form["HomeTeam"] if home else form["AwayTeam"],
                liveScore.get("homeTeamIcon" if home else "awayTeamIcon"),
                liveScore.get("homeTeamNickname" if home else "awayTeamNickname"),)
        except Exception:
            liveScore = await self._tryGetFinishedGameData(False)
            if not liveScore:
                liveScore = await self._requestLiveScoresJsonByMatchSafe()
            return Team.Build(liveScore.get("homeTeam" if home else "awayTeam"),
                              liveScore.get("homeTeamIcon" if home else "awayTeamIcon"),
                              liveScore.get("homeTeamNickname" if home else "awayTeamNickname"),
                              home)


    # GET


    def setScoreObserverInterval(self, intervalS: int) -> None:
        self._scoreObserverInterval = intervalS

    def addScoreObserver(self, observer: Coroutine) -> None:
        self._scoreObservers.append(observer)

    def removeScoreObserver(self, observer: Coroutine) -> None:
        self._scoreObservers.remove(observer)

    async def _observeScore(self) -> None:
        lastScore: Optional[Result] = None
        while True:
            try:
                if len(self._scoreObservers):
                    result = await self.currentScore()
                    if lastScore != result:
                        lastScore = result
                        for observer in self._scoreObservers:
                            await observer(self, lastScore)
            except:
                pass
            await asyncio.sleep(self._scoreObserverInterval)

    async def currentScore(self) -> Result:
        if not self._initialised:
            raise NotInitialisedException
        match = await self._requestLiveScoresJsonByMatchSafe(self._finished)
        assert match is not None # not in live scores anymore (finished some time ago) -> find other way
        return Result(match)

    async def startTime(self) -> datetime:
        if not self._initialised:
            raise NotInitialisedException
        match = await self._requestLiveScoresJsonByMatchSafe()
        return datetime.strptime(match["utcStartDate"], "%Y-%m-%dT%H:%M:%SZ")

    async def _started(self) -> bool:
        startTime = await self.startTime()
        return datetime.utcnow() >= startTime

    async def _finishedF(self) -> bool:
        if not self._initialised:
            await self.init()
        await self._requestLiveScoresJsonByMatchSafe(False)
        return self._finished

    async def state(self) -> MatchState:
        started, finished = await asyncio.gather(self._started(), self._finishedF())
        return MatchState.Parse(started, finished)

    async def venue(self) -> str:
        if not self._initialised:
            raise NotInitialisedException
        match = await self._requestLiveScoresJsonByMatchSafe()
        return match["matchLocation"]

    async def playByPlay(self) -> Optional[PlayByPlay]:
        try:
            resp = await pyfetch(self._getLink("GetPlayByPlayComponent"))
            jdata = await resp.json()
            return PlayByPlay(jdata)
        except Exception:
            return None

    async def homeTeam(self) -> Optional[Team]:
        if not self._initialised:
            raise NotInitialisedException
        return await self._getTeam(0, True)

    async def awayTeam(self) -> Optional[Team]:
        if not self._initialised:
            raise NotInitialisedException
        return await self._getTeam(1, False)

    @property
    def gallery(self) -> List[str]:
        return self._gallery

    async def report(self) -> Optional[MatchReport]:
        if not self._reportCache:
            self._reportCache = await asyncRunInThreadWithReturn(MatchReport, self._html)
        return self._reportCache or None

    async def duration(self) -> timedelta:
        if not self._initialised:
            raise NotInitialisedException
        if not await self._finishedF():
            startTime = await self.startTime()
            if datetime.utcnow() < startTime:
                return timedelta()
            return datetime.utcnow() - startTime
        if self._invalidMatchCentre:
            return timedelta()
        resp = await pyfetch(self._getLink("getlivescorehero"))
        jdata = await resp.json()
        return timedelta(minutes = float(jdata.get("Duration").split(" ")[0]))

    @property
    def matchCentreLink(self) -> str:
        return self._matchCentreLink

    async def watchLink(self) -> str:
        if not self._initialised:
            raise NotInitialisedException
        jdata = await self._requestLiveScoresJsonByMatchSafe()
        return jdata.get("watchLink") or None

    async def highlightsLink(self) -> str:
        if not self._highlightsLinkCache:
            if not self._initialised:
                raise NotInitialisedException
            jdata = await self._requestLiveScoresJsonByMatchSafe()
            self._highlightsLinkCache = jdata.get("highlightsLink") or None
        return self._highlightsLinkCache

    async def competition(self) -> Optional[Competition]:
        if self._invalidMatchCentre:
            jdata = await self._requestLiveScoresJsonByMatchSafe()
            competition = jdata.get("competition")
            if competition is None:
                return None
            return Competition({
                "Competition": competition.get("name"),
                "Leg": jdata.get("legName"),
                "Phase": jdata.get("phaseName"),
                "GroupPool": jdata.get("groupName"),
                "MatchNumber": jdata.get("matchNumber")
            })
        
        resp = await pyfetch(self._getLink("getlivescorehero"))
        jdata = await resp.json()
        return Competition(jdata)

    async def topPlayers(self) -> TopPlayers:
        topPlayers = TopPlayers()
        links = self._getLinks("GetTopStatisticsComponent")
        for link in links:
            resp = await pyfetch(link)
            jdata = await resp.json()
            topPlayers.append(TopPlayer(jdata))
        return topPlayers

    async def info(self) -> Info:
        if not self._infoCache:
            self._infoCache = await asyncRunInThreadWithReturn(Info, self._html)
        return self._infoCache or None


    # CREATE


    @staticmethod
    async def ByUrl(url: str) -> Match:
        resp = await pyfetch(url)
        return Match(await resp.string(), url)


    # CONVERT


    async def toJson(self) -> dict:
        return (await self.cache()).toJson()

    async def cache(self,) -> MatchCache:
        """
        gets a snapshot of the current data.
        takes about 1.2s and is thus significantly faster than
        direct queries of the properties
        """
                    # might allow selecting properties (in a future version)
                    #playByplay = True,
                    #competition = True,
                    #topPlayers = True,
                    #currentScore = True,
                    #duration = True,
                    #startTime = True,
                    #venue = True,
                    #homeTeam = True,
                    #awayTeam = True,
                    #watchLink = True,
                    #highlightsLink = True,
                    #finished = True,
                    #report = True,) -> MatchCache:
        afterInit = [ ]

        afterInit.append(self.playByPlay())
        afterInit.append(self.competition())
        afterInit.append(self.topPlayers())
        afterInit.append(self.report())
        afterInit.append(self.info())

        if not self._initialised:
            await self.init()

        afterInit.append(self.currentScore())
        afterInit.append(self.duration())
        afterInit.append(self.startTime())
        afterInit.append(self.venue())
        afterInit.append(self.homeTeam())
        afterInit.append(self.awayTeam())
        afterInit.append(self.watchLink())
        afterInit.append(self.highlightsLink())
        afterInit.append(self.state())
        afterInitResults = await asyncio.gather(*afterInit)
        t3 = time()

        return MatchCache(playByPlay= afterInitResults[0],
                          competition= afterInitResults[1],
                          topPlayers= afterInitResults[2],
                          gallery= self.gallery,
                          matchCentreLink= self._matchCentreLink,
                          currentScore= afterInitResults[5],
                          duration= afterInitResults[6],
                          startTime= afterInitResults[7],
                          venue= afterInitResults[8],
                          homeTeam= afterInitResults[9],
                          awayTeam= afterInitResults[10],
                          watchLink= afterInitResults[11],
                          highlightsLink= afterInitResults[12],
                          state= afterInitResults[13],
                          report= afterInitResults[3],
                          info= afterInitResults[4])
