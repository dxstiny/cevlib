from __future__ import annotations
from typing import Optional

from cevlib.helpers.dictTool import DictEx

from cevlib.types.iType import IType, JObject
from cevlib.types.types import CompetitionGender


class Competition(IType):
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        competition = dex.ensure("Competition", str)
        if "|" not in competition:
            competition += "|"
        self._name = competition.split("|")[0].removesuffix(" ")
        self._gender = CompetitionGender.Parse(competition.split("|")[1].removeprefix(" ").split(" ", maxsplit = 1)[0])
        self._groupPool = dex.ensure("GroupPool", str)
        self._leg = dex.ensure("Leg", str)
        self._phase = dex.ensure("Phase", str)
        self._season = dex.ensure("Season", str)
        self._matchNumber = dex.ensure("MatchNumber", str)
        self._logo = dex.ensure("CompetitionLogo", str)

    @staticmethod
    def BuildPlain(name: Optional[str] = None,
                   gender: CompetitionGender = CompetitionGender.Unknown,
                   groupPool: Optional[str] = None,
                   leg: Optional[str] = None,
                   phase: Optional[str] = None,
                   season: Optional[str] = None,
                   matchNumber: Optional[str] = None,
                   logo: Optional[str] = None) -> Competition:
        return Competition({
            "Competition": f"{name} | {gender.value}",
            "GroupPool": groupPool,
            "Leg": leg,
            "Phase": phase,
            "Season": season,
            "MatchNumber": matchNumber,
            "CompetitionLogo": logo
        })

    @property
    def name(self) -> str:
        return self._name

    @property
    def displayName(self) -> str:
        return f"{self._name} | {self._gender.value}"

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
        return f"(cevlib.types.competition.Competition) {self.displayName} ({self._matchNumber}) {self._season} > {self._phase} > {self._groupPool} ({self._leg})"

    @property
    def valid(self) -> bool:
        return None not in (self._name, self._gender)

    def toJson(self) -> JObject:
        return {
            "name": self.name,
            "displayName": self.displayName,
            "gender": self.gender.value,
            "groupPool": self.groupPool,
            "leg": self.leg,
            "phase": self.phase,
            "season": self.season,
            "logo": self.logo,
            "matchNumber": self.matchNumber
        }
