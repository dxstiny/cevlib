# cevlib
inofficial python library for cev.eu (NOT affiliated)

## Terms of Use
please refer to [cev.eu's Terms of Use](https://www.cev.eu/terms-of-use/)

The Owner undertakes its utmost effort to ensure that the content provided in this Application infringes no applicable legal provisions or third-party rights. However, it may not always be possible to achieve such a result.
In such cases, without prejudice to any legal prerogatives of Users to enforce their rights, Users are kindly asked to preferably report related complaints by opening an issue.

## TODOs
- observe scores (polling & subscription)
- read calendar (e.g. get matches)
- cleanup
- improve error handling
- tests :)
- test golden set
- provide examples
- info (how to attend, quotes, officials, etc.)

## Quick Start

```python
import asyncio

from cevlib.match import Match

async def main():
    match = await Match.ByUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2022/men/clm-61-cucine-lube-civitanova-v-ok-merkur-maribor/")

    print(await match.playByPlay())
    print(await match.competition())
    print(await match.topPlayers())
    print(await match.report())
    print(match.gallery) # Disclaimer: Photos featured on the CEV Photo Galleries are downloadable copyright free for media purposes only and only if CEV is credited as the source material. They are protected by copyright for all other commercial purposes. Those wishing to use CEV Photo Gallery photos for other commercial purposes should contact press@cev.eu
    print(match.matchCentreLink)

    await match.init()

    print(await match.currentScore())
    print(await match.duration())
    print(await match.startTime())
    print(await match.venue())
    print(await match.homeTeam())
    print(await match.watchLink())
    print(await match.highlightsLink())
    print(match.finished)

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
```
