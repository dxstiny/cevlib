# -*- coding: utf-8 -*-
"""cevlib"""
from __future__ import annotations
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from typing import Any, Dict, List, Optional, Tuple
import re
from bs4 import BeautifulSoup # type: ignore
from bs4.element import Tag # type: ignore

import aiohttp

from cevlib.calendar import CalendarMatch

from cevlib.helpers.dictTool import DictEx

from cevlib.types.competition import MatchCompetition
from cevlib.types.iType import IType
from cevlib.types.results import Result
from cevlib.types.team import Team
from cevlib.types.types import CompetitionGender


class Draw(IType):
    """competition draw. consists of two calendarMatches"""
    def __init__(self, matches: List[CalendarMatch]) -> None:
        self._matches = matches

        assert len(matches) == 2
        self._first, self._second = matches[0].teams

    def _sameTeams(self) -> bool:
        for match in self._matches:
            if self._first not in match.teams:
                return False
            if self._second not in match.teams:
                return False
        return True

    @property
    def competition(self) -> MatchCompetition:
        return self._matches[0].competition

    @property
    def firstTeam(self) -> Team:
        return self._first

    @property
    def secondTeam(self) -> Team:
        return self._second

    @property
    def teams(self) -> Tuple[Team, Team]:
        assert self.valid
        return self._matches[0].teams

    @property
    def matches(self) -> List[CalendarMatch]:
        assert self.valid
        return self._matches

    def get(self, index: int) -> Optional[CalendarMatch]:
        """matches[index]"""
        return self.matches[index] if index < len(self.matches) else None

    @property
    def valid(self) -> bool:
        return bool(self._matches) and self._sameTeams()

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Draw) {len(self._matches)} matches"

    def toJson(self) -> List[Dict[str, Any]]:
        if not self.valid:
            print(self._first, self._second, self._sameTeams())
        return [ match.toJson() for match in self._matches ]


class StandingsTeam(IType):
    """standings team"""
    def __init__(self, team: Dict[str, Any]) -> None:
        self._team = team

    @property
    def team(self) -> Dict[str, Any]:
        return self._team

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevlib.competitions.StandingsTeam) {self.team}"

    def toJson(self) -> Dict[str, Any]:
        return self._team


class StandingsPool(IType):
    """standings pool (i.e. group). consists of multiple standingsTeams"""
    def __init__(self, teams: List[StandingsTeam]) -> None:
        self._teams = teams

    @property
    def teams(self) -> List[StandingsTeam]:
        return self._teams

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevlib.competitions.StandingsPool) {len(self.teams)} teams"

    def toJson(self) -> List[Dict[str, Any]]:
        return [ team.toJson() for team in self.teams ]

class Standings(IType):
    """standings (e.g. score tables). consists of multiple standingsPools"""
    def __init__(self, table: Optional[Tag]) -> None:
        self._pools: List[StandingsPool] = [ ]
        if not table:
            return
        head = table.find("thead")
        bodies = table.find_all("tbody")
        if not head or len(bodies) == 0:
            return
        rows = head.find_all("tr")
        if len(rows) < 2:
            return
        headings1 = [ th.get_text(strip = True) for th in rows[0].find_all("th") ]
        headings1 = [ heading for heading in headings1 if heading ]
        headings1.insert(0, "")
        self._headings = [ ]
        headings1It = 0
        for th in rows[1].find_all("th"):
            assert isinstance(th, Tag)
            self._headings.append(f"{headings1[headings1It]}.{th.get_text(strip = True)}")
            if th.get("class") == ["u-pr-8"]:
                headings1It += 1

        if len(self._headings) == 0:
            return
        for body in bodies:
            teams: List[StandingsTeam] = [ ]
            for row in body.find_all("tr"):
                standing = { }
                for i, text in enumerate(row.find_all("td")):
                    standing[self._headings[i]] = text.get_text(strip = True)
                teams.append(StandingsTeam(standing))
            self._pools.append(StandingsPool(teams))

    @property
    def pools(self) -> List[StandingsPool]:
        return self._pools

    def get(self, index: int) -> Optional[StandingsPool]:
        """pools[index]"""
        if index >= len(self._pools):
            return None
        return self._pools[index]

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Standings) {len(self.pools)} pools"

    def toJson(self) -> List[List[Dict[str, Any]]]:
        return [ pool.toJson() for pool in self.pools ]


class Pool(IType):
    """round pool. consists of either standings or draws"""
    def __init__(self,
                 name: str,
                 draws: List[Draw],
                 standings: Optional[StandingsPool] = None) -> None:
        self._name = name
        self._draws = draws
        self._standings = standings

    def moveOrCreateDraw(self,
                         anyDrawTeam: Team,
                         newIndex: int,
                         competition: Optional[MatchCompetition]) -> None:
        if anyDrawTeam.name == "Bye":
            return
        oldIndex = -1
        for i, _ in enumerate(self._draws):
            if anyDrawTeam in self._draws[i].teams:
                oldIndex = i
                break

        if oldIndex >= 0:
            self._draws.insert(newIndex, self._draws.pop(oldIndex))
            return

        assert competition
        self._draws.insert(newIndex,
                           Draw([ CalendarMatch.shortcutMatch(competition, anyDrawTeam),
                                  CalendarMatch.shortcutMatch(competition, anyDrawTeam) ]))

    @property
    def valid(self) -> bool:
        return bool(self._name and len(self._draws))

    @property
    def standingsPool(self) -> Optional[StandingsPool]:
        return self._standings

    @property
    def draws(self) -> List[Draw]:
        return self._draws

    def get(self, index: int) -> Optional[Draw]:
        """draws[index]"""
        return self.draws[index] if index < len(self.draws) else None

    @property
    def name(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Pool) {self._name} ({len(self.draws)} draws) ({self.standingsPool})" # pylint: disable=line-too-long

    def toJson(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "draws": [ draw.toJson() for draw in self._draws ],
            "standings": self.standingsPool.toJson() if self.standingsPool else None
        }


class Round(IType):
    """competition round. consists of multiple pools."""
    def __init__(self, name: str, pools: List[Pool]) -> None:
        self._name = name
        self._pools = pools

    @property
    def valid(self) -> bool:
        return bool(self._name and len(self._pools))

    @property
    def name(self) -> str:
        return self._name

    @property
    def pools(self) -> List[Pool]:
        return self._pools

    def get(self, index: int) -> Optional[Pool]:
        """pools[index]"""
        return self.pools[index] if index < len(self.pools) else None

    @staticmethod
    def parsePool(pool: Dict[str, Any],
                  competition: CompetitionLink,
                  standings: Optional[StandingsPool]) -> Pool:
        pdex = DictEx(pool)
        draws: List[List[CalendarMatch]] = [ ]
        for match in pdex.ensureList("Results"):
            mdex = DictEx(match)
            homeId = 0
            awayId = 0
            try: # TODO safer regex solution
                homeId = int(re.search(r"^\/team\/([0-9]+)-[\w-]+$", match["HomeTeam"]["Link"]).group(1)) # type: ignore # pylint: disable=line-too-long
                awayId = int(re.search(r"^\/team\/([0-9]+)-[\w-]+$", match["AwayTeam"]["Link"]).group(1)) # type: ignore # pylint: disable=line-too-long
            except Exception as exc:
                print(exc)

            newMatch = CalendarMatch(mdex.ensureString("MatchCentreUrl"),
                MatchCompetition.buildPlain(competition.name,
                    competition.gender,
                    season = str(competition.age) if competition.age else None,
                    phase = pdex.ensure("Name", str),
                    matchNumber = mdex.ensure("MatchName", str)),
                Team.build(mdex.ensure("HomeTeam", DictEx).ensure("Name", str),
                    mdex.ensure("HomeTeam", DictEx).ensure("Logo", DictEx).ensure("Name", str),
                    "N/A",
                    True,
                    homeId),
                Team.build(mdex.ensure("AwayTeam", DictEx).ensure("Name", str),
                    mdex.ensure("AwayTeam", DictEx).ensure("Logo", DictEx).ensure("Name", str),
                    "N/A",
                    False,
                    awayId),
                mdex.ensureString("Location"),
                mdex.ensureString("MatchDateTime"),
                Result.parseFromForm(match),
                mdex.ensureBool("IsComplete"))
            newDraw = True
            for draw in draws:
                if draw[0].awayTeam.name == newMatch.homeTeam.name and \
                   draw[0].homeTeam.name == newMatch.awayTeam.name:
                    newDraw = False
                    draw.append(newMatch)
                    break
            if newDraw:
                draws.append([newMatch])
        return Pool(pdex.ensureString("Name"),
                    [ Draw(draw)
                      for draw in draws ],
                    standings)

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Round) {self._name} ({len(self.pools)} pools)"

    def toJson(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "pools": [ pool.toJson() for pool in self._pools ]
        }


class Competition(IType):
    """a single competition. consists of multiple rounds"""
    def __init__(self, rounds: List[Round]) -> None:
        self._rounds = rounds
        self._rearrangeDraws()

    def _rearrangeDraws(self) -> None:
        pools: List[Pool] = [ ]
        for round_ in self._rounds:
            pools.extend(round_.pools)
        for i in range(len(pools) - 1):
            pool = pools[- (i + 1)]
            previousPool = pools[- (i + 2)]
            if pool.standingsPool or previousPool.standingsPool:
                continue
            for j, _ in enumerate(pool.draws):
                previousPool.moveOrCreateDraw(pool.draws[j].firstTeam,
                                              j * 2, pool.draws[j].competition)
                previousPool.moveOrCreateDraw(pool.draws[j].secondTeam,
                                              j * 2 + 1, pool.draws[j].competition)

    @staticmethod
    def _parseRound(name: str,
                    pools: List[Dict[str, Any]],
                    competition: CompetitionLink,
                    standings: Optional[Standings] = None) -> Round:
        return Round(name,
                    [ Round.parsePool(pool,
                                      competition,
                                      standings.get(i) if standings else None)
                      for i, pool in enumerate(pools) ])

    @staticmethod
    async def fromUrl(url: str) -> Competition:
        """parse a competition from a url"""
        html = ""
        competition = (await Competitions.getAll()).getByLink(url)
        assert competition
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as resp:
                html = await resp.text()
        rounds = [ ]
        soup = BeautifulSoup(html, "html.parser")

        roundNameLookup = [ comp.get_text(strip = True)
                            for comp in soup.find_all("li", class_="tabs-title") ]

        #data-score-endpoint
        for i, comp in enumerate(soup.find_all("div", class_="competition-components-container")):
            if not isinstance(comp, Tag):
                continue
            linkDiv = comp.find("div", attrs = { "data-score-endpoint": True })
            if not isinstance(linkDiv, Tag):
                continue # has no useful content
            tableDiv = comp.find("div", class_="pool-standings-table")
            standings = Standings(tableDiv)
            link = "https:" + linkDiv["data-score-endpoint"]
            async with aiohttp.ClientSession() as client:
                async with client.get(link) as resp:
                    jdata = await resp.json(content_type=None)
                    name = roundNameLookup[i] if i <= len(roundNameLookup) else "N/A"
                    rounds.append(Competition._parseRound(name,
                                                          jdata.get("Pools"),
                                                          competition,
                                                          standings))
        return Competition(rounds)

    @property
    def rounds(self) -> List[Round]:
        """returns the rounds of the competition"""
        return self._rounds

    def get(self, index: int) -> Optional[Round]:
        """rounds[index]"""
        return self.rounds[index] if index < len(self.rounds) else None

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Competition) {len(self._rounds)} rounds"

    def toJson(self) -> List[Dict[str, Any]]:
        return [ round.toJson() for round in self._rounds ]


class CompetitionLink(IType):
    """minimal information about a competition"""
    def __init__(self, menuTitle: str, slabTitle: str, entry: str, href: str) -> None:
        self._href = href
        self._type = menuTitle
        self._name = slabTitle
        self._gender = CompetitionGender.parse(entry)
        self._age: Optional[int] = None

        if self._gender == CompetitionGender.Unknown:
            match = re.search(r'U([0-9]{2})([MW])', entry)
            assert match # TODO safer regex search solution
            age = match.group(1)
            gender = match.group(2)
            self._age = int(age) if age else None
            self._gender = CompetitionGender.parse(gender)

    @property
    def name(self) -> str:
        return self._name

    @property
    def type(self) -> str:
        return self._type

    @property
    def href(self) -> str:
        return self._href

    @property
    def gender(self) -> CompetitionGender:
        return self._gender

    @property
    def age(self) -> Optional[int]:
        return self._age

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevlib.competitions.CompetitionLink) {self.name} ({self.type}/{self.age}) {self._gender} ({self.href})" # pylint: disable=line-too-long

    def toJson(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "type": self._type,
            "gender": self._gender.value,
            "maxAge": self._age,
            "href": self._href
        }

    async def toCompetition(self) -> Competition:
        """cast to full competition"""
        return await Competition.fromUrl(self.href)


class Competitions(IType):
    """competitions wrapper (create with .getAll())"""
    _competitionsCache: List[CompetitionLink] = [ ]

    def __init__(self, html: str) -> None:
        self._competitions: List[CompetitionLink] = [ ]
        if len(Competitions._competitionsCache) > 0:
            self._competitions = Competitions._competitionsCache
            return
        soup = BeautifulSoup(html, "html.parser")
        for menuItem in soup.find_all("li", class_="c-nav__list__item"):
            if not isinstance(menuItem, Tag):
                continue
            menuTitleEl = menuItem.find("a", class_="menuItem")
            if not menuTitleEl:
                continue
            menuTitle = menuTitleEl.get_text(strip = True)

            for slab in menuItem.find_all("div", class_="menuSlab"):
                if not isinstance(slab, Tag):
                    continue
                for row in slab.find_all("div", class_="menuSlab__row"):
                    if not isinstance(row, Tag):
                        continue

                    for rowItem in row.find_all("div"):
                        titleEl = rowItem.find("a", class_="title")
                        if not titleEl:
                            continue

                        title = titleEl.get_text()

                        for item in rowItem.find_all("li"):
                            if not isinstance(item, Tag):
                                continue
                            atag = item.find("a")
                            if not atag:
                                continue
                            itemTitle = atag.attrs.get("title")
                            href = atag.attrs.get("href")

                            string = f"{menuTitle} - {title} - {itemTitle} ({href})"
                            canAppend = True
                            for block in [ "ranking", # TODO beach, snow, national
                                           "history",
                                           "multi-sport events",
                                           "latest",
                                           "beach",
                                           "snow",
                                           "nationals" ]:
                                if block in string.lower():
                                    canAppend = False
                                    continue
                            if canAppend:
                                self._competitions.append(CompetitionLink(menuTitle,
                                                                          title,
                                                                          itemTitle,
                                                                          href))

    @staticmethod
    async def getAll() -> Competitions:
        """get all competitions"""
        async with aiohttp.ClientSession() as client:
            async with client.get("https://www.cev.eu/") as resp:
                return Competitions(await resp.text())

    @property
    def valid(self) -> bool:
        return True

    def getByLink(self, link: str) -> Optional[CompetitionLink]:
        """get competitionLink (basic info) by link"""
        return next((item for item in self._competitions if item.href == link), None)

    @property
    def links(self) -> List[CompetitionLink]:
        """returns all competition links"""
        return self._competitions

    def get(self, index: int) -> Optional[CompetitionLink]:
        """links[index]"""
        return self.links[index] if index < len(self.links) else None

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Competitions) {self._competitions}"

    def toJson(self) -> List[Dict[str, Any]]:
        return [ competition.toJson() for competition in self._competitions ]
