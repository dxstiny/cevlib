# -*- coding: utf-8 -*-
"""cevlib"""
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from cevlib.helpers.dictTool import DictEx, ListEx

from cevlib.types.iType import JArray, JObject


class ScoreHeroToJson:
    """score hero endpoint to live scores endpoint data"""
    @staticmethod
    def convert(data: JObject, matchPollData: JArray) -> JObject:
        """convert"""
        dex = DictEx(data)
        pollData = ListEx(matchPollData)
        return {
            "matchLocation": dex.tryGet("StadiumInformation", str),
            "utcStartDate": dex.tryGet("MatchStartDateTimeUTC", str),
            "matchId": dex.ensure("MatchId", int),
            "homeSetsWon": dex.ensure("HomeTeam", DictEx).tryGet("Score", int),
            "awaySetsWon": dex.ensure("AwayTeam", DictEx).tryGet("Score", int),
            "hasGoldenSet": dex.ensure("GoldenSet", bool),
            "setResults": ScoreHeroToJson._convertSets(data),
            "matchState_String": "FINISHED",
            "matchNumber": "MatchNumber",
            "currentSetScore": {
                "homeScore": 0,
                "awayScore": 0,
                "setNumber": 0,
                "isInPlay": False
            },
            "homeTeam": dex.ensure("HomeTeam", DictEx).tryGet("Name", str),
            "awayTeam": dex.ensure("AwayTeam", DictEx).tryGet("Name", str),
            "homeTeamIcon": dex.ensure("HomeTeam", DictEx)
                               .ensure("Logo", DictEx).tryGet("Url", str),
            "awayTeamIcon": dex.ensure("AwayTeam", DictEx)
                               .ensure("Logo", DictEx).tryGet("Url", str),
            "homeTeamNickname": pollData.ensure(0, DictEx).tryGet("Value", str),
            "awayTeamNickname": pollData.ensure(1, DictEx).tryGet("Value", str),
            "homeTeamId": pollData.ensure(0, DictEx).tryGet("Id", int),
            "awayTeamId": pollData.ensure(1, DictEx).tryGet("Id", int)
        }

    @staticmethod
    def _convertSets(data: JObject) -> JArray:
        """convert sets"""
        mainSets = data["SetsFormatted"]\
                        .replace("<span>", "")\
                        .replace("</span>", "")\
                        .replace("(", "")\
                        .replace(")", "")\
                        .replace(" ", "")\
                        .split(",")
        goldenSet = data["GoldenSet"]
        sets = [ ]
        index = 1
        for mainSet in mainSets:
            if mainSet:
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
