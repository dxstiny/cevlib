# -*- coding: utf-8 -*-
"""cevlib"""
from __future__ import annotations
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

# (IMatch can be property or async)
# pylint: disable=invalid-overridden-method


import asyncio
from datetime import datetime, timedelta
import re
import json
from typing import Any, Coroutine, Dict, List, Optional, Callable
import aiohttp

from cevlib.exceptions import NotInitialisedException

from cevlib.helpers.asyncThread import asyncRunInThreadWithReturn
from cevlib.helpers.dictTool import DictEx, ListEx

from cevlib.converters.scoreHeroToJson import ScoreHeroToJson

from cevlib.types.competition import MatchCompetition
from cevlib.types.iMatch import IFullMatch
from cevlib.types.iType import JObject
from cevlib.types.info import Info
from cevlib.types.playByPlay import PlayByPlay
from cevlib.types.report import MatchReport
from cevlib.types.results import Result
from cevlib.types.stats import TeamStatistics, TopPlayer, TopPlayers
from cevlib.types.team import Team
from cevlib.types.types import MatchState


TScoreObserver = Callable[[Any, Any], Coroutine[Any, Any, Any]]


class MatchCache(IFullMatch):
    """snapshot of Match (all match data retrieved from Cache)"""
    def __init__(self,
                 playByPlay: Optional[PlayByPlay],
                 competition: Optional[MatchCompetition],
                 topPlayers: TopPlayers,
                 gallery: List[str],
                 matchCentreLink: str,
                 result: Result,
                 duration: timedelta,
                 startTime: datetime,
                 venue: str,
                 homeTeam: Team,
                 awayTeam: Team,
                 watchLink: Optional[str],
                 highlightsLink: Optional[str],
                 state: MatchState,
                 report: Optional[MatchReport],
                 info: Info) -> None:
        self._playByPlay = playByPlay
        self._competition = competition
        self._topPlayers = topPlayers
        self._gallery = gallery
        self._matchCentreLink = matchCentreLink
        self._result = result
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

    def toJson(self) -> JObject:
        return {
            "state": self.state.value,
            "result": self.result.toJson(),
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
    def finished(self) -> bool:
        return self.state == MatchState.Finished

    @property
    def competition(self) -> Optional[MatchCompetition]:
        return self._competition

    @property
    def playByPlay(self) -> Optional[PlayByPlay]:
        return self._playByPlay

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
    def result(self) -> Result:
        return self._result

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
    def watchLink(self) -> Optional[str]:
        return self._watchLink

    @property
    def highlightsLink(self) -> Optional[str]:
        return self._highlightsLink

    @property
    def state(self) -> MatchState:
        return self._state

    @property
    def report(self) -> Optional[MatchReport]:
        return self._report

    @property
    def info(self) -> Info:
        return self._info

    @staticmethod
    async def fromMatch(match: Match) -> MatchCache:
        """create a snapshot of this match"""
        return await match.cache()

    def __repr__(self) -> str:
        return f"(cevlib.match.MatchCache) {self.toJson()}"


class Match(IFullMatch):
    """match class"""
    def __init__(self, html: str, url: str) -> None:
        self._invalidMatchCentre = "This page can be replaced with a custom 404. Check the documentation for" in html or \
                                   "Object reference not set to an instance of an object." in html # pylint: disable=line-too-long
        #if self._invalidMatchCentre:
            #raise AttributeError("404")
        self._umbracoLinks = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*umbraco[\w.,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ] # pylint: disable=line-too-long
        self._gallery = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*Upload\/Photo\/[\w .,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-]).(jpg|JPG)", html) ] # pylint: disable=line-too-long
        embeddedVideos = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*\/embed\/[\w .,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ] # pylint: disable=line-too-long
        self._highlightsLinkCache: Optional[str] = None
        if len(embeddedVideos):
            self._highlightsLinkCache = "https://" + embeddedVideos[0].replace("/embed/", "/v/") \
                                                                      .split("?")[0]
        #self._nodeId = self._getParameter(self._getLink("livescorehero"), "nodeId")
        self._html = html
        self._matchId: Optional[int] = None
        self._liveScoresCache: Optional[JObject] = None
        self._formCache: Optional[JObject] = None
        self._finished = False
        self._matchCentreLink: str = url
        self._initialised = False
        self._reportCache: Optional[MatchReport] = None
        self._infoCache: Optional[Info] = None
        self._scoreObservers: List[TScoreObserver] = [ ]
        self._scoreObserverInterval = 20
        self._init = asyncio.create_task(self._startInit())
        asyncio.create_task(self._observeScore())

    @property
    def valid(self) -> bool:
        return bool(self._umbracoLinks)

    async def _startInit(self) -> None:
        self._matchId = await self._getMatchId()
        self._initialised = True

    def init(self) -> asyncio.Task[None]:
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


#    def _getParameter(self, link: str, parameter: str) -> Optional[str]:
#        try:
#            return "0"
#            # TODO working?? (not indexable)
#            #return re.search(f"(?<={parameter}=)([A-Za-z0-9]*)(?=&)?", link)[0]
#        except:
#            return None

    def _getLinks(self, contains: str) -> List[str]:
        eligibleLinks = [ ]
        for umbracoLink in self._umbracoLinks:
            if contains in umbracoLink:
                eligibleLinks.append("https://" + umbracoLink.replace("amp;", ""))
        return eligibleLinks

    def _getLink(self, contains: str, index: int = 0) -> str:
        links = self._getLinks(contains)
        if len(links) > index:
            return links[index]
        return ""

    async def _getForm(self) -> JObject:
        if self._formCache is None:
            async with aiohttp.ClientSession() as client:
                async with client.get(self._getLink("GetFormComponent")) as resp:
                    self._formCache = json.loads(await resp.json(content_type=None))
        return self._formCache

    async def _getMatchId(self) -> Optional[int]:
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(self._getLink("livescorehero")) as resp:
                    jdata = await resp.json(content_type=None)
                    return int(jdata.get("MatchId"))
        except: # pylint: disable=bare-except
            return None

    async def _requestLiveScoresJson(self, useCache: bool = True) -> JObject:
        if useCache and self._liveScoresCache:
            return self._liveScoresCache
        async with aiohttp.ClientSession() as client:
            async with client.get("https://www.cev.eu/LiveScores.json") as resp:
                jdata = DictEx(await resp.json(content_type=None))
                self._liveScoresCache = jdata
                return jdata

    async def _requestLiveScoresJsonByMatchSafe(self, useCache: bool = True) ->  Optional[JObject]:
        return await (self._requestLiveScoresJsonByMatchId(useCache) if not self._invalidMatchCentre
                      else self._requestLiveScoresJsonByMatchCentreLink(useCache))

    async def _requestLiveScoresJsonByMatchCentreLink(self,
                                                      useCache: bool = True) -> Optional[JObject]:
        assert self._matchCentreLink
        jdata = DictEx(await self._requestLiveScoresJson(useCache))
        for competition in jdata.ensure("competitions", ListEx).iterate(DictEx):
            for match in competition.ensure("matches", ListEx).iterate(DictEx):
                if match.ensure("matchCentreLink", str) == self._matchCentreLink:
                    self._finished = match.ensure("matchState_String", str) == "FINISHED"
                    match["competition"] = { "name": competition.tryGet("competitionName", str),
                                            "id": competition.tryGet("competitionId", int) }
                    return match
        return await self._tryGetFinishedGameData()

    async def _requestLiveScoresJsonByMatchId(self, useCache: bool = True) -> Optional[JObject]:
        assert self._matchId
        jdata = DictEx(await self._requestLiveScoresJson(useCache))
        for competition in jdata.ensure("competitions", ListEx).iterate(DictEx):
            for match in competition.ensure("matches", ListEx).iterate(DictEx):
                if match.ensure("matchId", int) == self._matchId:
                    self._finished = match.ensure("matchState_String", str) == "FINISHED"
                    return match
        return await self._tryGetFinishedGameData()

    async def _tryGetFinishedGameData(self, trulyFinished: bool = True) -> Optional[JObject]:
        if self._invalidMatchCentre:
            return None
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
                liveScore = DictEx(await self._requestLiveScoresJsonByMatchSafe())
                form = await self._getForm()
                return Team(teamData,
                            playerStatsData,
                            TeamStatistics(teamStatsData, home),
                            matchPoll,
                            form["HomeTeam"] if home else form["AwayTeam"],
                            liveScore.ensure("homeTeamIcon" if home
                                             else "awayTeamIcon", str),
                            liveScore.ensure("homeTeamNickname" if home
                                             else "awayTeamNickname", str),)
        except Exception:
            liveScore = DictEx(await self._tryGetFinishedGameData(False))
            if not liveScore:
                liveScore = DictEx(await self._requestLiveScoresJsonByMatchSafe())
            return Team.build(liveScore.ensure("homeTeam" if home else "awayTeam",
                                               str),
                              liveScore.ensure("homeTeamIcon" if home else "awayTeamIcon",
                                               str),
                              liveScore.ensure("homeTeamNickname" if home else "awayTeamNickname",
                                               str),
                              home)


    # GET


    def setScoreObserverInterval(self, intervalS: int) -> None:
        """the interval the score observer uses"""
        self._scoreObserverInterval = intervalS

    def addScoreObserver(self, observer: TScoreObserver) -> None:
        """adds a new score observer"""
        self._scoreObservers.append(observer)

    def removeScoreObserver(self, observer: TScoreObserver) -> None:
        """removes a score observer"""
        self._scoreObservers.remove(observer)

    async def _observeScore(self) -> None:
        lastScore: Optional[Result] = None
        while True:
            try:
                if len(self._scoreObservers) > 0:
                    result = await self.result()
                    if lastScore != result:
                        lastScore = result
                        for observer in self._scoreObservers:
                            await observer(self, lastScore)
            except: # pylint: disable=bare-except
                pass
            await asyncio.sleep(self._scoreObserverInterval)

    async def result(self) -> Result:
        if not self._initialised:
            raise NotInitialisedException
        match = await self._requestLiveScoresJsonByMatchSafe(self._finished)
        # TODO not in live scores anymore (finished some time ago) -> find other way
        assert match is not None
        return Result(match)

    async def startTime(self) -> datetime:
        if not self._initialised:
            raise NotInitialisedException
        match = DictEx(await self._requestLiveScoresJsonByMatchSafe())
        return datetime.strptime(match.ensure("utcStartDate", str), "%Y-%m-%dT%H:%M:%SZ")

    async def _started(self) -> bool:
        startTime = await self.startTime()
        return datetime.utcnow() >= startTime

    async def _finishedF(self) -> bool:
        if not self._initialised:
            await self.init()
        await self._requestLiveScoresJsonByMatchSafe(False)
        return self._finished

    async def finished(self) -> bool:
        return await self._finishedF()

    async def state(self) -> MatchState:
        started, finished = await asyncio.gather(self._started(), self._finishedF())
        return MatchState.parse(started, finished)

    async def venue(self) -> str:
        if not self._initialised:
            raise NotInitialisedException
        match = DictEx(await self._requestLiveScoresJsonByMatchSafe())
        return match.ensure("matchLocation", str)

    async def playByPlay(self) -> Optional[PlayByPlay]:
        try:
            async with aiohttp.ClientSession() as client:
                async with client.get(self._getLink("GetPlayByPlayComponent")) as resp:
                    jdata = await resp.json(content_type=None)
                    return PlayByPlay(jdata)
        except Exception:
            return None

    async def homeTeam(self) -> Team:
        if not self._initialised:
            raise NotInitialisedException
        team = await self._getTeam(0, True)
        assert team
        return team

    async def awayTeam(self) -> Team:
        if not self._initialised:
            raise NotInitialisedException
        team = await self._getTeam(1, False)
        assert team
        return team

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
        async with aiohttp.ClientSession() as client:
            async with client.get(self._getLink("getlivescorehero")) as resp:
                jdata = await resp.json(content_type=None)
                return timedelta(minutes = float(jdata.get("Duration").split(" ")[0]))

    @property
    def matchCentreLink(self) -> str:
        return self._matchCentreLink

    async def watchLink(self) -> Optional[str]:
        if not self._initialised:
            raise NotInitialisedException
        jdata = DictEx(await self._requestLiveScoresJsonByMatchSafe())
        return jdata.tryGet("watchLink", str)

    async def highlightsLink(self) -> Optional[str]:
        if not self._highlightsLinkCache:
            if not self._initialised:
                raise NotInitialisedException
            jdata = DictEx(await self._requestLiveScoresJsonByMatchSafe())
            self._highlightsLinkCache = jdata.tryGet("highlightsLink", str)
        return self._highlightsLinkCache

    async def competition(self) -> Optional[MatchCompetition]:
        if self._invalidMatchCentre:
            jdata = DictEx(await self._requestLiveScoresJsonByMatchSafe())
            competition = jdata.ensure("competition", DictEx)
            if not competition:
                return None
            return MatchCompetition({
                "Competition": competition.ensure("name", str),
                "Leg": jdata.ensure("legName", str),
                "Phase": jdata.ensure("phaseName", str),
                "GroupPool": jdata.ensure("groupName", str),
                "MatchNumber": jdata.ensure("matchNumber", str)
            })
        async with aiohttp.ClientSession() as client:
            async with client.get(self._getLink("getlivescorehero")) as resp:
                jdata = await resp.json(content_type=None)
                assert jdata is not None
                return MatchCompetition(jdata)

    async def topPlayers(self) -> TopPlayers:
        topPlayers = TopPlayers()
        links = self._getLinks("GetTopStatisticsComponent")
        for link in links:
            async with aiohttp.ClientSession() as client:
                async with client.get(link) as resp:
                    jdata = await resp.json(content_type=None)
                    topPlayers.append(TopPlayer(jdata))
        return topPlayers

    async def info(self) -> Info:
        if self._infoCache is None:
            self._infoCache = await asyncRunInThreadWithReturn(Info, self._html)
        assert self._infoCache
        return self._infoCache


    # CREATE


    @staticmethod
    async def byUrl(url: str) -> Match:
        """creates a match by match url (link/href)"""
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as resp:
                return Match(await resp.text(), url)


    # CONVERT


    async def toJson(self) -> Dict[str, Any]:
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
        afterInit: List[Coroutine[Any, Any, Any]] = [ ]

        afterInit.append(self.playByPlay())
        afterInit.append(self.competition())
        afterInit.append(self.topPlayers())
        afterInit.append(self.report())
        afterInit.append(self.info())

        if not self._initialised:
            await self.init()

        afterInit.append(self.result())
        afterInit.append(self.duration())
        afterInit.append(self.startTime())
        afterInit.append(self.venue())
        afterInit.append(self.homeTeam())
        afterInit.append(self.awayTeam())
        afterInit.append(self.watchLink())
        afterInit.append(self.highlightsLink())
        afterInit.append(self.state())
        afterInitResults = await asyncio.gather(*afterInit)

        return MatchCache(playByPlay= afterInitResults[0],
                          competition= afterInitResults[1],
                          topPlayers= afterInitResults[2],
                          gallery= self.gallery,
                          matchCentreLink= self._matchCentreLink,
                          result= afterInitResults[5],
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
