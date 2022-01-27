from __future__ import annotations
from typing import Optional
import aiohttp
import re


class MatchCentre:
    def __init__(self, html: str) -> None:
        self._umbracoLinks = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*umbraco[\w.,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        self._nodeId = self._getParameter(self._getLink("livescorehero"), "nodeId")
        self._matchId: Optional[int] = None

    def _getParameter(self, link: str, parameter: str) -> str:
        return re.search(f"(?<={parameter}=)([A-Za-z0-9]*)(?=&)?", link)[0]

    def _getLink(self, contains: str) -> str:
        for umbracoLink in self._umbracoLinks:
            if contains in umbracoLink:
                return "https://" + umbracoLink.replace("amp;", "")

    async def init(self) -> None:
        self._matchId = await self._getMatchId()

    async def _getMatchId(self) -> str:
        async with aiohttp.ClientSession() as client:
            async with client.get(self._getLink("livescorehero")) as resp:
                jdata = await resp.json(content_type=None)
                return int(jdata.get("MatchId"))

    async def currentScore(self) -> str:
        assert self._matchId
        async with aiohttp.ClientSession() as client:
            async with client.get("https://cev.eu/LiveScores.json") as resp:
                jdata = await resp.json()
                for competition in jdata["competitions"]:
                    for match in competition["matches"]:
                        if match["matchId"] == self._matchId:
                            return match["setResults"]

    @staticmethod
    async def ByUrl(url: str) -> MatchCentre:
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as resp:
                return MatchCentre(await resp.text())
