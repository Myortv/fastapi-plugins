import asyncio

from plugins.controllers import DatabaseManager as DM

loop = asyncio.get_event_loop()

loop.run_until_complete(
	DM.start('games')
)
print(DM.Config.POOL)
