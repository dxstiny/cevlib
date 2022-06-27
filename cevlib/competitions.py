from __future__ import annotations
from typing import List, Optional, Tuple
import re
from bs4 import BeautifulSoup # type: ignore
from bs4.element import Tag # type: ignore

import aiohttp
from cevlib.calendar import CalendarMatch

from cevlib.types.competition import Competition as CompetitionModel
from cevlib.types.iType import IType
from cevlib.types.results import Result
from cevlib.types.team import Team
from cevlib.types.types import CompetitionGender


class Draw(IType):
    def __init__(self, matches: List[CalendarMatch]) -> None:
        self._matches = matches
        self._first: Optional[Team] = None
        self._second: Optional[Team] = None

        if len(self._matches):
            self._first, self._second = matches[0].teams

    def _sameTeams(self) -> bool:
        for match in self._matches:
            if self._first not in match.teams:
                return False
            if self._second not in match.teams:
                return False
        return True

    @property
    def competition(self) -> CompetitionModel:
        return self._matches[0].competition

    @property
    def firstTeam(self) -> Team:
        return self._first

    @property
    def secondTeam(self) -> Team:
        return self._second

    @property
    def teams(self) -> Tuple[Team]:
        assert self.valid
        return self._matches[0].teams

    @property
    def matches(self) -> List[CalendarMatch]:
        assert self.valid
        return self._matches

    def get(self, index: int) -> Optional[Pool]:
        """matches[index]"""
        return self.matches[index] if index < len(self.matches) else None

    @property
    def valid(self) -> bool:
        return len(self._matches) and self._sameTeams()
    
    def __repr__(self) -> str:
        return f"(cevlib.competitions.Draw) {len(self._matches)} matches"

    def toJson(self) -> dict:
        if not self.valid:
            print(self._first, self._second, self._sameTeams())
        return [ match.toJson() for match in self._matches ]


class StandingsTeam(IType):
    def __init__(self, team: dict) -> None:
        self._team = team

    @property
    def team(self) -> dict:
        return self._team

    @property
    def valid(self) -> bool:
        return True
    
    def __repr__(self) -> str:
        return f"(cevlib.competitions.StandingsTeam) {self.team}"

    def toJson(self) -> dict:
        return self._team


class StandingsPool(IType):
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

    def toJson(self) -> dict:
        return [ team.toJson() for team in self.teams ]

class Standings(IType):
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

    def get(self, index) -> Optional[List[dict]]:
        """pools[index]"""
        if index >= len(self.pools):
            return None
        return self.pools[index]

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Standings) {len(self.pools)} pools"

    def toJson(self) -> dict:
        return [ pool.toJson() for pool in self.pools ]


class Pool(IType):
    def __init__(self, name: str, draws: List[Draw], standings: Optional[StandingsPool] = None) -> None:
        self._name = name
        self._draws = draws
        self._standings = standings

    def moveOrCreateDraw(self, anyDrawTeam: Team, newIndex: int, competition: Optional[CompetitionModel]) -> None:
        if anyDrawTeam.name == "Bye":
            return
        oldIndex = -1
        for i in range(len(self._draws)):
            if anyDrawTeam in self._draws[i].teams:
                oldIndex = i
                break

        if oldIndex >= 0:
            self._draws.insert(newIndex, self._draws.pop(oldIndex))
            return

        assert competition
        self._draws.insert(newIndex, Draw([ CalendarMatch.ShortcutMatch(competition, anyDrawTeam), CalendarMatch.ShortcutMatch(competition, anyDrawTeam) ]))

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
        return f"(cevlib.competitions.Pool) {self._name} ({len(self.draws)} draws) ({self.standingsPool})"

    def toJson(self) -> dict:
        return {
            "name": self._name,
            "draws": [ draw.toJson() for draw in self._draws ],
            "standings": self.standingsPool.toJson() if self.standingsPool else None
        }


class Round(IType):
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
    def ParsePool(pool: dict, competition: CompetitionLink, standings: Optional[Standings]):
        draws: List[List[CalendarMatch]] = [ ]
        for match in pool.get("Results"):
            homeId = 0
            awayId = 0
            try:
                homeId = int(re.search(r"^\/team\/([0-9]+)-[\w-]+$", match["HomeTeam"]["Link"]).group(1))
                awayId = int(re.search(r"^\/team\/([0-9]+)-[\w-]+$", match["AwayTeam"]["Link"]).group(1))
            except Exception as e:
                print(e)

            newMatch = CalendarMatch(match.get("MatchCentreUrl"),
                                     CompetitionModel.BuildPlain(competition.name, competition.gender,
                                                                 season = str(competition.age) if competition.age else None,
                                                                 phase = pool.get("Name"), matchNumber = match.get("MatchName")),
                                     Team.Build(match["HomeTeam"]["Name"], match["HomeTeam"]["Logo"]["Url"], "N/A", True, homeId),
                                     Team.Build(match["AwayTeam"]["Name"], match["AwayTeam"]["Logo"]["Url"], "N/A", False, awayId),
                                     match.get("Location"),
                                     match.get("MatchDateTime"),
                                     Result.ParseFromForm(match),
                                     match.get("IsComplete"))
            newDraw = True
            for draw in draws:
                if draw[0].awayTeam.name == newMatch.homeTeam.name and draw[0].homeTeam.name == newMatch.awayTeam.name:
                    newDraw = False
                    draw.append(newMatch)
                    break
            if newDraw:
                draws.append([newMatch])
        return Pool(pool.get("Name"), [ Draw([ match for match in draw ]) for draw in draws ], standings)

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Round) {self._name} ({len(self.pools)} pools)"

    def toJson(self) -> dict:
        return {
            "name": self._name,
            "pools": [ pool.toJson() for pool in self._pools ]
        }


class Competition(IType):
    def __init__(self, rounds: List[Round]) -> None:
        self._rounds = rounds
        self._rearrangeDraws()
    
    def _rearrangeDraws(self) -> None:
        pools: List[Pool] = [ ]
        [ pools.extend(round.pools) for round in self._rounds ]
        for i in range(len(pools) - 1):
            pool = pools[- (i + 1)]
            previousPool = pools[- (i + 2)]
            if pool.standingsPool or previousPool.standingsPool:
                continue
            for j in range(len(pool.draws)):
                previousPool.moveOrCreateDraw(pool.draws[j].firstTeam, j * 2, pool.draws[j].competition)
                previousPool.moveOrCreateDraw(pool.draws[j].secondTeam, j * 2 + 1, pool.draws[j].competition)

    @staticmethod
    def _ParseRound(name: str, pools: List[dict], competition: CompetitionLink, standings: Optional[Standings] = None) -> Round:
        return Round(name, [ Round.ParsePool(pool, competition, standings.get(i) if standings else None) for i, pool in enumerate(pools) ])

    @staticmethod
    async def FromUrl(url: str) -> Competition:
        html = ""
        competition = (await Competitions.GetAll()).getByLink(url)
        assert competition
        async with aiohttp.ClientSession() as client:
            async with client.get(url) as resp:
                html = await resp.text()
        #links = [ "https://" + match[0].replace("&amp;", "&") for match in re.finditer(r"([\w_-]+(?:(?:\.[\w_-]+)+))([\w.,@;?^=%&:\/~+#-]*GetResultList?[\w .,@;?^=%&:\/~+#-]*[\w@?^=%&\/~+#-])", html) ]
        rounds = [ ]
        soup = BeautifulSoup(html, "html.parser")

        roundNameLookup = [ comp.get_text(strip = True) for comp in soup.find_all("li", class_="tabs-title") ]

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
                    rounds.append(Competition._ParseRound(name, jdata.get("Pools"), competition, standings))
        return Competition(rounds)
    
    @property
    def rounds(self) -> List[Round]:
        return self._rounds

    def get(self, index: int) -> Optional[Round]:
        """rounds[index]"""
        return self.rounds[index] if index < len(self.rounds) else None

    @property
    def valid(self) -> bool:
        return True

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Competition) {len(self._rounds)} rounds"
    
    def toJson(self) -> dict:
        return [ round.toJson() for round in self._rounds ]


class CompetitionLink(IType):
    def __init__(self, menuTitle: str, slabTitle: str, entry: str, href: str) -> None:
        self._href = href
        self._type = menuTitle
        self._name = slabTitle
        self._gender = CompetitionGender.Parse(entry)
        self._age: Optional[int] = None

        if self._gender == CompetitionGender.Unknown:
            match = re.search(r'U([0-9]{2})([MW])', entry)
            age = match.group(1)
            gender = match.group(2)
            self._age = int(age) if age else None
            self._gender = CompetitionGender.Parse(gender)

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
        return f"(cevlib.competitions.CompetitionLink) {self.name} ({self.type}/{self.age}) {self._gender} ({self.href})"

    def toJson(self) -> dict:
        return {
            "name": self._name,
            "type": self._type,
            "gender": self._gender.value,
            "maxAge": self._age,
            "href": self._href
        }

    async def toCompetition(self) -> Competition:
        return await Competition.FromUrl(self.href)


class Competitions(IType):
    _competitionsCache: List[CompetitionLink] = [ ]

    def __init__(self, html) -> None:
        if len(Competitions._competitionsCache) > 0:
            self._competitions = Competitions._competitionsCache
            return
        soup = BeautifulSoup(html, "html.parser")
        self._competitions: List[CompetitionLink] = [ ]
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
                            a = item.find("a")
                            if not a:
                                continue
                            itemTitle = a.attrs.get("title")
                            href = a.attrs.get("href")

                            string = f"{menuTitle} - {title} - {itemTitle} ({href})"
                            canAppend = True
                            for block in [ "ranking", "history", "multi-sport events", "latest", "beach", "snow", "nationals" ]: # TODO beach, snow, national
                                if block in string.lower():
                                    canAppend = False
                                    continue
                            if canAppend:
                                self._competitions.append(CompetitionLink(menuTitle, title, itemTitle, href))
        
    @staticmethod
    async def GetAll() -> Competitions:
        async with aiohttp.ClientSession() as client:
            async with client.get(f"https://www.cev.eu/") as resp:
                return Competitions(await resp.text())
    
    @property
    def valid(self) -> bool:
        return True

    def getByLink(self, link: str) -> Optional[Competition]:
        return next((item for item in self._competitions if item.href == link), None)

    @property
    def links(self) -> List[CompetitionLink]:
        return self._competitions

    def get(self, index: int) -> Optional[CompetitionLink]:
        """links[index]"""
        return self.links[index] if index < len(self.links) else None

    def __repr__(self) -> str:
        return f"(cevlib.competitions.Competitions) {self._competitions}"

    def toJson(self) -> dict:
        return [ competition.toJson() for competition in self._competitions ]
