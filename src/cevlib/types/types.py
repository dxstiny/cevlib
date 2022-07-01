# -*- coding: utf-8 -*-
"""cevlib"""
from __future__ import annotations
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from enum import Enum

class TeamStatisticType(Enum):
    """all possible team statistics"""
    WinningSpikes = "winningSpikes"
    KillBlocks = "killBlocks"
    Aces = "aces"
    OpponentErrors = "opponentErrors"
    Points = "points"
    Unknown = "unknown"

    @staticmethod
    def parse(value: str) -> TeamStatisticType:
        """parse by value"""
        if value == "Winning Spikes":
            return TeamStatisticType.WinningSpikes
        if value == "Kill Blocks":
            return TeamStatisticType.KillBlocks
        if value == "Aces":
            return TeamStatisticType.Aces
        if value == "Opponent Errors":
            return TeamStatisticType.OpponentErrors
        if value == "Points":
            return TeamStatisticType.Points
        return TeamStatisticType.Unknown


class TopPlayerType(Enum):
    """all 'top player' awards"""
    Scorer = "scorer"
    Attacker = "attacker"
    Blocker = "blocker"
    Server = "server"
    Receiver = "receiver"
    Unknown = "unknown"

    @staticmethod
    def parse(value: str) -> TopPlayerType:
        """parse by value"""
        if value == "Scorer":
            return TopPlayerType.Scorer
        if value == "Attacker":
            return TopPlayerType.Attacker
        if value == "Blocker":
            return TopPlayerType.Blocker
        if value == "Server":
            return TopPlayerType.Server
        if value == "Receiver":
            return TopPlayerType.Receiver
        return TopPlayerType.Unknown


class CompetitionGender(Enum):
    """gender of the competition"""
    Women = "Women"
    Men = "Men"
    Unknown = "Unknown"

    @staticmethod
    def parse(value: str) -> CompetitionGender:
        """parse by value"""
        if value in ("Women", "W"):
            return CompetitionGender.Women
        if value in ("Men", "M"):
            return CompetitionGender.Men
        return CompetitionGender.Unknown


class Position(Enum):
    """all player positions"""
    Setter = "setter"
    MiddleBlocker = "middleBlocker"
    OutsideSpiker = "outsideSpiker"
    Opposite = "opposite"
    Libero = "libero"
    HeadCoach = "headCoach"
    Unknown = "unknown"

    @staticmethod
    def parse(value: str) -> Position:
        """parse by value"""
        if value == "Setter":
            return Position.Setter
        if value == "Middle blocker":
            return Position.MiddleBlocker
        if value == "Outside spiker":
            return Position.OutsideSpiker
        if value == "Opposite":
            return Position.Opposite
        if value == "Libero":
            return Position.Libero
        if value == "Head Coach":
            return Position.HeadCoach
        return Position.Unknown


class Zone(Enum):
    """all zones"""
    One = 1
    Two = 2
    Three = 3
    Four = 4
    Five = 5
    Six = 6
    Sub = 0
    Featured = 7
    Unknown = -1

    @staticmethod
    def parse(value: int) -> Zone:
        """parse by value"""
        if value == 1:
            return Zone.One
        if value == 2:
            return Zone.Two
        if value == 3:
            return Zone.Three
        if value == 4:
            return Zone.Four
        if value == 5:
            return Zone.Five
        if value == 6:
            return Zone.Six
        if value in (7, 8):
            return Zone.Featured
        if value == 0:
            return Zone.Sub
        return Zone.Unknown


class PlayType(Enum):
    """all types of 'play by play'"""
    Spike = "spike"
    Serve = "serve"
    Block = "block"
    FirstServe = "firstServe"
    Unknown = "unknown"

    @staticmethod
    def parse(typeName: str) -> PlayType:
        """parse by value"""
        if typeName == "Spike":
            return PlayType.Spike
        if typeName == "Serve":
            return PlayType.Serve
        if typeName == "Block":
            return PlayType.Block
        if typeName == "First Serve":
            return PlayType.FirstServe
        return PlayType.Unknown


class MatchState(Enum):
    """state of the match"""
    Upcoming = "upcoming"
    Live = "live"
    Finished = "finished"
    Unknown = "unknown"

    @staticmethod
    def parse(started: bool, finished: bool) -> MatchState:
        """determine"""
        if not started and not finished:
            return MatchState.Upcoming
        if started and not finished:
            return MatchState.Live
        if finished:
            return MatchState.Finished
        return MatchState.Unknown
