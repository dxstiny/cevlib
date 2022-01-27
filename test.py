import asyncio
import aiohttp

from MatchCentre import MatchCentre

async def main():
    x = await MatchCentre.ByUrl("https://www.cev.eu/match-centres/2022-european-cups/cev-volleyball-challenge-cup-2022-women/chcw-73-panathinaikos-ac-athens-v-cv-tenerife-la-laguna")
    await x.init()
    print(await x.currentScore())
    print(x._matchId)
    print(x)

asyncio.run(main())