# -*- coding: utf-8 -*-
"""cevlib"""
from __future__ import annotations
__copyright__ = ("Copyright (c) 2022 https://github.com/dxstiny")

from typing import List, Optional, Union
from bs4 import BeautifulSoup # type: ignore
from bs4.element import Tag, NavigableString # type: ignore

from cevlib.types.iType import IType, JObject


class MatchReport(IType):
    """match report"""
    def __init__(self, html: str) -> None:
        soup = BeautifulSoup(html, "html.parser")
        self._quotes: List[MatchQuote] = [ ]
        self._inNumbers: List[MatchInNumber]  = [ ]
        self._body: Optional[str] = None
        self._headline: Optional[str] = None
        try:
            matchReport = soup.find("div", class_="match-report")
            try:
                self._headline = str(matchReport.h2.get_text(strip=True))
                self._body = str(matchReport.find("div",
                                                  class_="match-report__summary-container").p.text)
            except Exception:
                self._headline = None
                self._body = None

            matchReport.decompose()
            matchReport = soup.find("div", class_="match-report")
            self._quotes = MatchQuote.parse(soup)
            self._inNumbers = MatchInNumber.parse(matchReport)
        except AttributeError:
            self._headline = None
            self._body = None
            self._quotes = [ ]
            self._inNumbers = [ ]

    def toJson(self) -> JObject:
        return {
            "headline": self.headline,
            "body": self.body,
            "quotes": [ quote.toJson() for quote in self.quotes ],
            "inNumbers": [ inNumber.toJson() for inNumber in self.inNumbers ]
        }

    @property
    def headline(self) -> Optional[str]:
        """headline"""
        assert self.valid
        return self._headline

    @property
    def body(self) -> Optional[str]:
        """body content"""
        assert self.valid
        return self._body

    @property
    def quotes(self) -> List[MatchQuote]:
        """match quotes"""
        assert self.valid
        return self._quotes

    @property
    def inNumbers(self) -> List[MatchInNumber]:
        """fancy stats (e.g. minutes played, attendance, ...)"""
        assert self.valid
        return self._inNumbers

    @property
    def valid(self) -> bool:
        return None not in (self._headline, self._body) and\
               len(self._quotes) > 0 or \
               len(self._inNumbers) > 0

    def __repr__(self) -> str:
        return f"(cevlib.types.report.MatchQuote) {self._headline} ({self._body})\n{self._quotes}\n{self._inNumbers}" # pylint: disable=line-too-long


class MatchInNumber(IType):
    """fancy stats (e.g. minutes played, attendance, ...)"""
    def __init__(self, value: str, title: str, description: str) -> None:
        self._value = value
        self._title = title
        self._description = description

    def toJson(self) -> JObject:
        return {
            "title": self.title,
            "description": self.description,
            "value": self.value
        }

    @property
    def valid(self) -> bool:
        return None not in (self._value, self._title, self._description)

    @property
    def value(self) -> str:
        """the 'number'"""
        assert self.valid
        return self._value

    @property
    def title(self) -> str:
        """stat name"""
        assert self.valid
        return self._title

    @property
    def description(self) -> str:
        """description/explanation"""
        assert self.valid
        return self._description

    def __repr__(self) -> str:
        return f"(cevlib.types.report.MatchInNumber) {self._title}: {self._value} ({self._description})" # pylint: disable=line-too-long

    @staticmethod
    def parse(soup: Union[Tag, NavigableString]) -> List[MatchInNumber]:
        """parse from html tag"""
        numbers = soup.find_all("div", class_="column-container")
        matchInNumbers: List[MatchInNumber] = [ ]
        for number in numbers:
            title = number.find("span", class_="col__content-title").get_text(strip=True)
            matchInNumbers.append(MatchInNumber(number.span.text,
                                                title,
                                                number.p.text))
        return matchInNumbers


class MatchQuote(IType):
    """match quote"""
    def __init__(self, quote: str, cite: str) -> None:
        self._quote = quote.replace("“", "").replace("”", "").removeprefix(" ").removesuffix(" ")
        self._cite = cite.split("<br>")[0]
        self._citeDescription = cite.split("<br>")[1]

    def toJson(self) -> JObject:
        return {
            "quote": self.quote,
            "cite": self.cite,
            "citeDescription": self.citeDescription
        }

    @property
    def quote(self) -> str:
        """the quote itself"""
        assert self.valid
        return self._quote

    @property
    def cite(self) -> str: # TODO rename to source?
        """cite/source"""
        assert self.valid
        return self._cite

    @property
    def citeDescription(self) -> str:
        """description of the cite/source"""
        assert self.valid
        return self._citeDescription

    @property
    def valid(self) -> bool:
        return None not in (self._quote, self._cite, self._citeDescription)

    def __repr__(self) -> str:
        return f"(cevlib.types.report.MatchQuote) {self._cite} ({self._citeDescription}): '{self._quote}'" # pylint: disable=line-too-long

    @staticmethod
    def parse(soup: BeautifulSoup) -> List[MatchQuote]:
        """parses a quote from html"""
        quotes: List[MatchQuote] = [ ]
        quoteElements = soup.find_all(class_="quote-block")
        for element in quoteElements:
            quotes.append(MatchQuote(element.p.text,
                                     element.cite.get_text(strip=True, separator='<br>')))
        return quotes
