from abc import abstractmethod
from cevlib.types.competition import Competition
from cevlib.types.iType import IType
from cevlib.types.team import Team
from cevlib.types.types import MatchState

class IMatch(IType):
    @property
    @abstractmethod
    def state(self) -> MatchState:
        """state of the match"""

    @property
    @abstractmethod
    def competition(self) -> Competition:
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
    def homeTeam(self) -> str:
        """match href"""
