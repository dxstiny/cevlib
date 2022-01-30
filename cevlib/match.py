from __future__ import annotations
from datetime import datetime, timedelta
from typing import List, Optional
import aiohttp
import re
import json
from cevlib.helpers.asyncThread import asyncRunInThreadWithReturn
from cevlib.types.competition import Competition

from cevlib.types.playByPlay import PlayByPlay
from cevlib.types.report import MatchReport
from cevlib.types.results import Result, SetResult
from cevlib.types.stats import TeamStatistics, TopPlayer, TopPlayers
from cevlib.types.team import Team
from cevlib.converters.scoreHeroToJson import ScoreHeroToJson


class Match:
    def __init__(self, html: str, url: str) -> None:
        self._umbracoLinks = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*umbraco[\w.,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        self._gallery = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*Upload/Photo/[\w.,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        self._nodeId = self._getParameter(self._getLink("livescorehero"), "nodeId")
        self._html = html
        self._report: Optional[MatchReport] = None
        self._matchId: Optional[int] = None
        self._liveScoresCache: Optional[dict] = None
        self._formCache: Optional[dict] = None
        self._finished = False
        self._matchCentreLink = url

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
        - report
        """
        self._matchId = await self._getMatchId()
        self._report = await asyncRunInThreadWithReturn(MatchReport, self._html)


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

    async def _tryGetFinishedGameData(self) -> Optional[dict]:
        async with aiohttp.ClientSession() as client:
            self._finished = True
            livescorehero = { }
            matchpolldata = [ ]
            async with client.get(self._getLink("getlivescorehero")) as resp:
                livescorehero = await resp.json(content_type=None)
            async with client.get(self._getLink("GetMatchPoll")) as resp:
                matchpolldata = await resp.json(content_type=None)
            return ScoreHeroToJson.convert(livescorehero, matchpolldata)

    async def _getTeam(self, index: int, home: bool) -> Team:
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


    # GET


    async def currentScore(self) -> List[SetResult]:
        match = await self._requestLiveScoresJsonByMatchId(self._finished)
        assert match is not None # not in live scores anymore (finished some time ago) -> find other way
        return Result(match)

    async def startTime(self) -> datetime:
        match = await self._requestLiveScoresJsonByMatchId()
        return datetime.strptime(match["utcStartDate"], "%Y-%m-%dT%H:%M:%SZ")

    async def venue(self) -> str:
        match = await self._requestLiveScoresJsonByMatchId()
        return match["matchLocation"]

    async def playByPlay(self) -> PlayByPlay:
        async with aiohttp.ClientSession() as client:
            async with client.get(self._getLink("GetPlayByPlayComponent")) as resp:
                jdata = await resp.json(content_type=None)
                return PlayByPlay(jdata)

    async def matchPoll(self) -> PlayByPlay:
        async with aiohttp.ClientSession() as client:
            async with client.get(self._getLink("GetMatchPoll")) as resp:
                jdata = await resp.json(content_type=None)
                return PlayByPlay(jdata)

    async def homeTeam(self) -> Team:
        return await self._getTeam(0, True)

    async def awayTeam(self) -> Team:
        return await self._getTeam(1, False)

    @property
    def finished(self) -> bool:
        return self._finished

    @property
    def gallery(self) -> List[str]:
        return self._gallery

    @property
    def report(self) -> MatchReport:
        assert self._report
        return self._report

    async def duration(self) -> timedelta:
        if not self._finished:
            return datetime.utcnow() - await self.startTime()
        async with aiohttp.ClientSession() as client:
            async with client.get(self._getLink("getlivescorehero")) as resp:
                jdata = await resp.json(content_type=None)
                return timedelta(minutes = float(jdata.get("Duration").split(" ")[0]))

    @property
    def matchCentreLink(self) -> str:
        return self._matchCentreLink

    async def watchLink(self) -> str:
        jdata = await self._requestLiveScoresJsonByMatchId()
        return jdata.get("watchLink")

    async def highlightsLink(self) -> str:
        jdata = await self._requestLiveScoresJsonByMatchId()
        return jdata.get("highlightsLink")

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
