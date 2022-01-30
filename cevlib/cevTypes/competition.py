from __future__ import annotations
from enum import Enum
from cevlib.cevTypes.iType import IType


class CompetitionGender(Enum):
    Women = "Women"
    Men = "Men"
    Unknown = "Unknown"

    def Parse(value: str) -> CompetitionGender:
        if value == "Women":
            return CompetitionGender.Women
        if value == "Men":
            return CompetitionGender.Men
        return CompetitionGender.Unknown

class Competition(IType):
    def __init__(self, data: dict) -> None:
        self._competitionName = data.get("Competition").split("|")[0].removesuffix(" ")
        self._gender = CompetitionGender.Parse(data.get("Competition").split("|")[1].removeprefix(" "))
        self._groupPool = data.get("GroupPool")
        self._leg = data.get("Leg")
        self._phase = data.get("Phase")
        self._season = data.get("Season")
        self._matchNumber = data.get("MatchNumber")
        self._logo = data.get("CompetitionLogo")

    @property
    def competition(self) -> str:
        return self._competitionName

    @property
    def competitionDisplayName(self) -> str:
        return f"{self._competitionName} | {self._gender.value}"

    @property
    def gender(self) -> CompetitionGender:
        return self._gender

    @property
    def groupPool(self) -> str:
        return self._groupPool

    @property
    def leg(self) -> str:
        return self._leg

    @property
    def phase(self) -> str:
        return self._phase

    @property
    def season(self) -> str:
        return self._season

    @property
    def matchNumber(self) -> str:
        return self._matchNumber

    @property
    def logo(self) -> str:
        return self._logo

    def __repr__(self) -> str:
        return f"(cevTypes.competition.Competition) {self.competitionDisplayName} ({self._matchNumber}) {self._season} > {self._phase} > {self._groupPool} ({self._leg})"

    @property
    def valid(self) -> bool:
        return None not in (self._competitionName, self._gender, self._matchNumber)
