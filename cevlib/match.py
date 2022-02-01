from __future__ import annotations
import asyncio
from datetime import datetime, timedelta
from time import time
from typing import Callable, Coroutine, List, Optional
import aiohttp
import re
import json
from cevlib.exceptions import NotInitialisedException
from cevlib.helpers.asyncThread import asyncRunInThreadWithReturn
from cevlib.types.competition import Competition
from cevlib.types.iType import IType

from cevlib.types.playByPlay import PlayByPlay
from cevlib.types.report import MatchReport
from cevlib.types.results import Result
from cevlib.types.stats import TeamStatistics, TopPlayer, TopPlayers
from cevlib.types.team import Team
from cevlib.converters.scoreHeroToJson import ScoreHeroToJson
from cevlib.types.types import MatchState


class MatchCache(IType):
    def __init__(self,
                 playByPlay: Optional[PlayByPlay],
                 competition: Competition,
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
                 report: Optional[MatchReport]) -> None:
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

    def toJson(self) -> dict:
        return {
            "playByPlay": self.playByPlay.toJson() if self.playByPlay else None,
            "competition": self.competition.toJson(),
            "topPlayers": self.topPlayers.toJson(),
            "gallery": self.gallery,
            "currentScore": self.currentScore.toJson(),
            "matchCentreLink": self.matchCentreLink,
            "watchLink": self.watchLink,
            "highlightsLink": self.highlightsLink,
            "duration": str(self.duration),
            "startTime": str(self.startTime),
            "venue": self.venue,
            "homeTeam": self.homeTeam.toJson(),
            "awayTeam": self.awayTeam.toJson(),
            "report": self.report.toJson() if self.report else None,
            "state": self.state.value
        }

    @property
    def valid(self) -> bool:
        return True

    @property
    def playByPlay(self) -> PlayByPlay:
        return self._playByPlay

    @property
    def competition(self) -> Competition:
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


class Match(IType):
    def __init__(self, html: str, url: str) -> None:
        self._umbracoLinks = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*umbraco[\w.,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        self._gallery = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*Upload/Photo/[\w.,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        self._nodeId = self._getParameter(self._getLink("livescorehero"), "nodeId")
        self._html = html
        self._matchId: Optional[int] = None
        self._liveScoresCache: Optional[dict] = None
        self._formCache: Optional[dict] = None
        self._finished = False
        self._matchCentreLink = url
        self._initialised = False
        self._reportCache: Optional[MatchReport] = None
        self._scoreObservers: List[Coroutine] = [ ]
        self._scoreObserverInterval = 20
        asyncio.create_task(self._observeScore())

    @property
    def valid(self) -> bool:
        return len(self._umbracoLinks) and self._matchCentreLink is not None

    async def init(self) -> None:
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
        self._matchId = await self._getMatchId()
        self._initialised = True


    # HELPERS


    def _getParameter(self, link: str, parameter: str) -> str:
        return re.search(f"(?<={parameter}=)([A-Za-z0-9]*)(?=&)?", link)[0]

    def _getLinks(self, contains: str) -> str:
        eligibleLinks = [ ]
        for umbracoLink in self._umbracoLinks:
            if contains in umbracoLink:
                eligibleLinks.append("https://" + umbracoLink.replace("amp;", ""))
        return eligibleLinks

    def _getLink(self, contains: str, index: int = 0) -> str:
        return self._getLinks(contains)[index]

    async def _getForm(self) -> dict:
        if not self._formCache:
            async with aiohttp.ClientSession() as client:
                async with client.get(self._getLink("GetFormComponent")) as resp:
                    self._formCache = json.loads(await resp.json(content_type=None))
        return self._formCache

    async def _getMatchId(self) -> str:
        async with aiohttp.ClientSession() as client:
            async with client.get(self._getLink("livescorehero")) as resp:
                jdata = await resp.json(content_type=None)
                return int(jdata.get("MatchId"))

    async def _requestLiveScoresJson(self, useCache = True) -> dict:
        if useCache and self._liveScoresCache:
            return self._liveScoresCache
        async with aiohttp.ClientSession() as client:
            async with client.get("https://cev.eu/LiveScores.json") as resp:
                jdata = await resp.json()
                self._liveScoresCache = jdata
                return jdata

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
        async with aiohttp.ClientSession() as client:
            self._finished = trulyFinished
            livescorehero = { }
            matchpolldata = [ ]
            async with client.get(self._getLink("getlivescorehero")) as resp:
                livescorehero = await resp.json(content_type=None)
            async with client.get(self._getLink("GetMatchPoll")) as resp:
                matchpolldata = await resp.json(content_type=None)
            return ScoreHeroToJson.convert(livescorehero, matchpolldata)

    async def _getTeam(self, index: int, home: bool) -> Optional[Team]:
        try:
            async with aiohttp.ClientSession() as client:
                playerStatsData = { }
                teamData = { }
                teamStatsData = { }
                matchPoll = [ ]
                async with client.get(self._getLink("GetStartingTeamComponent", index)) as resp:
                    teamData = await resp.json(content_type=None)
                async with client.get(self._getLink("GetPlayerStatsComponentMC")) as resp:
                    playerStatsData = json.loads(await resp.json(content_type=None))
                async with client.get(self._getLink("GetTeamStatsComponentMC")) as resp:
                    teamStatsData = json.loads(await resp.json(content_type=None))
                async with client.get(self._getLink("GetMatchPoll")) as resp:
                    matchPoll = await resp.json(content_type=None)
                liveScore = await self._requestLiveScoresJsonByMatchId()
                form = await self._getForm()
                return Team(teamData, playerStatsData, TeamStatistics(teamStatsData, home), matchPoll,
                    form["HomeTeam"] if home else form["AwayTeam"],
                    liveScore.get("homeTeamIcon" if home else "awayTeamIcon"),
                    liveScore.get("homeTeamNickname" if home else "awayTeamNickname"),)
        except IndexError:
            liveScore = await self._tryGetFinishedGameData(False)
            return Team({ "TeamLogo": {
                            "AltText": liveScore.get("homeTeam" if home else "awayTeam"),
                            "Url": liveScore.get("homeTeamIcon" if home else "awayTeamIcon")
                        } },
                    { }, TeamStatistics({ }, home), [ ],
                    { } if home else { },
                    liveScore.get("homeTeamIcon" if home else "awayTeamIcon"),
                    liveScore.get("homeTeamNickname" if home else "awayTeamNickname"),)
            return None


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
            if len(self._scoreObservers):
                result = await self.currentScore()
                if lastScore != result:
                    lastScore = result
                    for observer in self._scoreObservers:
                        await observer(lastScore)
            await asyncio.sleep(self._scoreObserverInterval)

    async def currentScore(self) -> Result:
        if not self._initialised:
            raise NotInitialisedException
        match = await self._requestLiveScoresJsonByMatchId(self._finished)
        assert match is not None # not in live scores anymore (finished some time ago) -> find other way
        return Result(match)

    async def startTime(self) -> datetime:
        if not self._initialised:
            raise NotInitialisedException
        match = await self._requestLiveScoresJsonByMatchId()
        return datetime.strptime(match["utcStartDate"], "%Y-%m-%dT%H:%M:%SZ")

    async def _started(self) -> bool:
        startTime = await self.startTime()
        return datetime.utcnow() >= startTime

    async def _finishedF(self) -> bool:
        if not self._initialised:
            await self.init()
        await self._requestLiveScoresJsonByMatchId()
        return self._finished

    async def state(self) -> MatchState:
        started, finished = await asyncio.gather(self._started(), self._finishedF())
        return MatchState.Parse(started, finished)

    async def venue(self) -> str:
        if not self._initialised:
            raise NotInitialisedException
        match = await self._requestLiveScoresJsonByMatchId()
        return match["matchLocation"]

    async def playByPlay(self) -> Optional[PlayByPlay]:
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(self._getLink("GetPlayByPlayComponent")) as resp:
                    jdata = await resp.json(content_type=None)
                    return PlayByPlay(jdata)
        except IndexError:
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
        if not self._finished:
            startTime = await self.startTime()
            if datetime.utcnow() < startTime:
                return timedelta()
            return datetime.utcnow() - startTime
        async with aiohttp.ClientSession() as client:
            async with client.get(self._getLink("getlivescorehero")) as resp:
                jdata = await resp.json(content_type=None)
                return timedelta(minutes = float(jdata.get("Duration").split(" ")[0]))

    @property
    def matchCentreLink(self) -> str:
        return self._matchCentreLink

    async def watchLink(self) -> str:
        if not self._initialised:
            raise NotInitialisedException
        jdata = await self._requestLiveScoresJsonByMatchId()
        return jdata.get("watchLink") or None

    async def highlightsLink(self) -> str:
        if not self._initialised:
            raise NotInitialisedException
        jdata = await self._requestLiveScoresJsonByMatchId()
        return jdata.get("highlightsLink") or None

    async def competition(self) -> Competition:
        async with aiohttp.ClientSession() as client:
            async with client.get(self._getLink("getlivescorehero")) as resp:
                jdata = await resp.json(content_type=None)
                return Competition(jdata)

    async def topPlayers(self) -> TopPlayers:
        topPlayers = TopPlayers()
        links = self._getLinks("GetTopStatisticsComponent")
        for link in links:
            async with aiohttp.ClientSession() as client:
                async with client.get(link) as resp:
                    jdata = await resp.json(content_type=None)
                    topPlayers.append(TopPlayer(jdata))
        return topPlayers


    # CREATE


    @staticmethod
    async def ByUrl(url: str) -> Match:
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as resp:
                return Match(await resp.text(), url)


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

        return MatchCache(afterInitResults[0],
                          afterInitResults[1],
                          afterInitResults[2],
                          self.gallery,
                          self._matchCentreLink,
                          afterInitResults[4],
                          afterInitResults[5],
                          afterInitResults[6],
                          afterInitResults[7],
                          afterInitResults[8],
                          afterInitResults[9],
                          afterInitResults[10],
                          afterInitResults[11],
                          afterInitResults[12],
                          afterInitResults[3])
