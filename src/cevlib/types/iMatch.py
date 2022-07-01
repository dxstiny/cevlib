# -*- coding: utf-8 -*-
"""cevlib"""
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from abc import abstractmethod
from datetime import datetime, timedelta
from typing import Any, Coroutine, List, Optional, TypeVar, Union

from cevlib.types.competition import MatchCompetition
from cevlib.types.iType import IType
from cevlib.types.playByPlay import PlayByPlay
from cevlib.types.results import Result
from cevlib.types.team import Team
from cevlib.types.types import MatchState
from cevlib.types.stats import TopPlayers
from cevlib.types.report import MatchReport
from cevlib.types.info import Info


T = TypeVar("T")
FunOrProp = Union[Coroutine[Any, Any, T], T]


class IMatch(IType):
    """simple match interface"""
    @abstractmethod
    def state(self) -> FunOrProp[MatchState]:
        """state of the match"""

    @abstractmethod
    def finished(self) -> FunOrProp[bool]:
        """match finished?"""

    @abstractmethod
    def competition(self) -> FunOrProp[Optional[MatchCompetition]]:
        """competition"""

    @abstractmethod
    def homeTeam(self) -> FunOrProp[Team]:
        """home team"""

    @abstractmethod
    def awayTeam(self) -> FunOrProp[Team]:
        """away team"""

    @abstractmethod
    def venue(self) -> FunOrProp[str]:
        """venue / location"""

    @abstractmethod
    def startTime(self) -> FunOrProp[datetime]:
        """start time"""

    @abstractmethod
    def result(self) -> FunOrProp[Result]:
        """result"""

    @abstractmethod
    def matchCentreLink(self) -> Optional[str]:
        """match href"""


class IFullMatch(IMatch):
    """full match interface"""
    @abstractmethod
    def playByPlay(self) -> FunOrProp[Optional[PlayByPlay]]:
        """play by play component (match commentary)"""

    @abstractmethod
    def gallery(self) -> List[str]:
        """photo gallery"""

    @abstractmethod
    def topPlayers(self) -> FunOrProp[TopPlayers]:
        """best players"""

    @abstractmethod
    def duration(self) -> FunOrProp[timedelta]:
        """match duration"""

    @abstractmethod
    def watchLink(self) -> FunOrProp[Optional[str]]:
        """stream link"""

    @abstractmethod
    def highlightsLink(self) -> FunOrProp[Optional[str]]:
        """highlights link"""

    @abstractmethod
    def report(self) -> FunOrProp[Optional[MatchReport]]:
        """match report"""

    @abstractmethod
    def info(self) -> FunOrProp[Info]:
        """match info"""
