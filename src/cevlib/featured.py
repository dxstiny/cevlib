# -*- coding: utf-8 -*-
"""cevlib"""
from __future__ import annotations
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")


from typing import List
import re

import aiohttp

from cevlib.types.iType import IType, JObject


class Featured(IType):
    """featured news, images, ..."""
    def __init__(self) -> None:
        self._gallery: List[str] = [ ]
        self._videos: List[str] = [ ]

    async def init(self) -> None:
        """init"""
        async with aiohttp.ClientSession() as client:
            async with client.get("https://www.cev.eu/") as resp:
                html = await resp.text()
        self._gallery = [ f"https://www.cev.eu{match[0]}"
                          for match in re.finditer(r"(\/media\/[\w .,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-]).(jpg|JPG)", html) ] # pylint: disable=line-too-long
        self._videos = [ f"https://{match[0].replace('/embed/', '/v/').split('?')[0]}"
                         for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*\/embed\/[\w .,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ] # pylint: disable=line-too-long

    @property
    def gallery(self) -> List[str]:
        """gallery"""
        return self._gallery

    @property
    def videos(self) -> List[str]:
        """videos"""
        return self._videos

    def toJson(self) -> JObject:
        return {
            "gallery": self.gallery,
            "videos": self.videos
        }

    @property
    def valid(self) -> bool:
        return True
