import discord
from discord.ext import commands

class Honeypot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.api.get_plugin_partition(self)
        self.config = None

    async def cog_load(self):
        self.config = await self.db.find_one({"_id": "honeypot"})

    async def update_config(self):
        await self.db.find_one_and_update(
            {"_id": "honeypot"},
            {"$set": self.config},
            upsert=True,
        )

async def setup(bot):
    await bot.add_cog(Honeypot(bot))