import asyncio
from cevlib.calendar import Calendar

async def main():
    matches = await Calendar.matchesOfMonth(3, 2022) # get all matches of march, 2022
    print( matches )

    matches = await Calendar.upcomingMatches() # get approximately 10 upcoming (or running) games
    # these matches are displayed on cev.eu under "GameHub/Match List"
    print( matches )

    matches = await Calendar.recentMatches() # get approximately 10 recently finished games
    # these matches are displayed on cev.eu under "GameHub/Recent Results"
    print( matches )

    matches = await Calendar.upcomingAndRecentMatches() # get both Upcoming & Recent matches (faster than running them separately)
    # these matches are displayed on cev.eu under "GameHub"
    print( matches )

    x = await matches[0].toMatch() # any CalendarMatch object can be cast to a "full" Match (full capabilities), a match centre link is currently required though
    # if no match centre link exists for this match, toMatch returns None
    if x:
        print( await x.cache() )

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
asyncio.run(main())
