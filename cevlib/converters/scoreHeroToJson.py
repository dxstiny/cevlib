class ScoreHeroToJson:
    @staticmethod
    def convert(data: dict) -> dict:
        return {
            "matchLocation": data["StadiumInformation"],
            "utcStartDate": data["MatchStartDateTimeUTC"],
            "matchId": int(data["MatchId"]),
            "homeSetsWon": data["HomeTeam"]["Score"],
            "awaySetsWon": data["AwayTeam"]["Score"],
            "hasGoldenSet": True if data["GoldenSet"] else False,
            "setResults": ScoreHeroToJson._convertSets(data),
            "matchState_String": "FINISHED",
            "matchNumber": "MatchNumber",
            "currentSetScore": {
                "homeScore": 0,
                "awayScore": 0,
                "setNumber": 0,
                "isInPlay": False
            }
        }

    @staticmethod
    def _convertSets(data: dict) -> list:
        mainSets = data["SetsFormatted"].replace("<span>", "").replace("</span>", "").replace("(", "").replace(")", "").replace(" ", "").split(",")
        goldenSet = data["GoldenSet"]
        sets = [ ]
        index = 1
        for mainSet in mainSets:
            sets.append({
                "homeScore": mainSet.split("-")[0],
                "awayScore": mainSet.split("-")[1],
                "setNumber": index,
                "isInPlay": False
            })
            index += 1
        if goldenSet:
            sets.append({
                "homeScore": goldenSet.split("-")[0],
                "awayScore": goldenSet.split("-")[1],
                "setNumber": index,
                "isInPlay": False
            })
        return sets
