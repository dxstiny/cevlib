from __future__ import annotations
import aiohttp
import re


class MatchCentre:
    def __init__(self, html: str) -> None:
        self._umbracoLinks = [ match[0] for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*umbraco[\w.,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        self._nodeId = self._getParameter(self._getLink("livescorehero"), "nodeId")
        print(self._nodeId)

    def _getParameter(self, link: str, parameter: str) -> str:
        return re.search(f"(?<={parameter}=)([A-Za-z0-9]*)(?=&)?", link)[0]

    def _getLink(self, contains: str) -> str:
        for umbracoLink in self._umbracoLinks:
            if contains in umbracoLink:
                return umbracoLink

    @staticmethod
    async def ByUrl(url: str) -> MatchCentre:
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as resp:
                assert resp.status == 200
                return MatchCentre(await resp.text())
