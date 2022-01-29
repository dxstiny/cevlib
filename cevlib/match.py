from __future__ import annotations
from datetime import datetime
from typing import List, Optional
import aiohttp
import re
import json

from cevlib.cevTypes.playByPlay import PlayByPlay
from cevlib.cevTypes.results import SetResult
from cevlib.cevTypes.stats import TeamStatistics
from cevlib.cevTypes.team import Team


class Match:
    def __init__(self, html: str) -> None:
        self._umbracoLinks = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*umbraco[\w.,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        self._nodeId = self._getParameter(self._getLink("livescorehero"), "nodeId")
        self._matchId: Optional[int] = None
        self._liveScoresCache: Optional[dict] = None

    def _getParameter(self, link: str, parameter: str) -> str:
        return re.search(f"(?<={parameter}=)([A-Za-z0-9]*)(?=&)?", link)[0]

    def _getLink(self, contains: str, index: int = 0) -> str:
        for umbracoLink in self._umbracoLinks:
            if contains in umbracoLink:
                if not index == 0:
                    index -= 1
                    continue
                return "https://" + umbracoLink.replace("amp;", "")

    async def init(self) -> None:
        self._matchId = await self._getMatchId()

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

    async def _requestLiveScoresJsonByMatchId(self, useCache = True) -> dict:
        assert self._matchId
        jdata = await self._requestLiveScoresJson(useCache)
        for competition in jdata["competitions"]:
            for match in competition["matches"]:
                if match["matchId"] == self._matchId:
                    return match

    async def currentScore(self) -> str:
        match = await self._requestLiveScoresJsonByMatchId(False)
        assert match is not None # not in live scores anymore (finished some time ago) -> find other way
        return SetResult.ParseList(match["setResults"])

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

    async def homeTeam(self) -> Team:
        return await self._getTeam(0, True)

    async def awayTeam(self) -> Team:
        return await self._getTeam(1, False)

    async def _getTeam(self, index: int, home: bool) -> Team:
        async with aiohttp.ClientSession() as client:
            playerStatsData = { }
            teamData = { }
            teamStatsData = { }
            async with client.get(self._getLink("GetStartingTeamComponent", index)) as resp:
                teamData = await resp.json(content_type=None)
            async with client.get(self._getLink("GetPlayerStatsComponentMC")) as resp:
                playerStatsData = json.loads(await resp.json(content_type=None))
            async with client.get(self._getLink("GetTeamStatsComponentMC")) as resp:
                teamStatsData = json.loads(await resp.json(content_type=None))
            return Team(teamData, playerStatsData, TeamStatistics(teamStatsData, home))

    @staticmethod
    async def ByUrl(url: str) -> Match:
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as resp:
                return Match(await resp.text())
