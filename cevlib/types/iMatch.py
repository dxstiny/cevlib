# -*- coding: utf-8 -*-
"""cevlib"""
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from abc import abstractmethod
from datetime import datetime
from typing import Optional

from cevlib.types.competition import MatchCompetition
from cevlib.types.iType import IType
from cevlib.types.results import Result
from cevlib.types.team import Team
from cevlib.types.types import MatchState

class IMatch(IType):
    """simple match interface"""
    @property
    @abstractmethod
    def state(self) -> MatchState:
        """state of the match"""

    @property
    @abstractmethod
    def finished(self) -> bool:
        """match finished?"""

    @property
    @abstractmethod
    def competition(self) -> Optional[MatchCompetition]:
        """competition"""

    @property
    @abstractmethod
    def homeTeam(self) -> Team:
        """home team"""

    @property
    @abstractmethod
    def awayTeam(self) -> Team:
        """away team"""

    @property
    @abstractmethod
    def venue(self) -> str:
        """venue / location"""

    @property
    @abstractmethod
    def startTime(self) -> datetime:
        """start time"""

    @property
    @abstractmethod
    def result(self) -> Result:
        """result"""

    @property
    @abstractmethod
    def matchCentreLink(self) -> Optional[str]:
        """match href"""
