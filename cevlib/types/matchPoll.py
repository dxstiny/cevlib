from cevlib.helpers.dictTool import DictEx
from cevlib.types.iType import IType, JObject

class TeamPoll(IType):
    def __init__(self, data: JObject) -> None:
        dex = DictEx(data)
        self._percent: float = dex.ensure("Percent", float)
        self._count: int = dex.ensure("VoteCount", int)

    def toJson(self) -> JObject:
        return {
            "percent": self.percent,
            "count": self.count
        }

    def __repr__(self) -> str:
        return f"(cevlib.types.matchPoll.TeamPoll) {self._count} ({self._percent})"

    @property
    def percent(self) -> float:
        return self._percent
    
    @property
    def count(self) -> int:
        return self._count

    @property
    def valid(self) -> bool:
        return None not in (self._percent, self._count)
