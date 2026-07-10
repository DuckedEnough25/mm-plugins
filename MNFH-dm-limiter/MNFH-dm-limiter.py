from discord.ext import commands


def message_check(message):
    if message.author.bot:
        return False
    elif message.channel.id not in (721750845749723236, 1065831118970040340):
        return False
    elif message.author.guild_permissions.manage_messages:
        return False
    elif len(message.message_snapshots) == 0:
        return len(message.content) > 100
    return len(message.message_snapshots[0].content) > 100

class MNFHDMLimiter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message_check(message):
            await message.reply("This channel is only for asking people to DM with you. Intro's or other long messages are not allowed.", delete_after=10)
            await message.delete()

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if message_check(after):
            await after.reply("This channel is only for asking people to DM with you. Intro's or other long messages are not allowed.", delete_after=10)
            await after.delete()

async def setup(bot):
    await bot.add_cog(MNFHDMLimiter(bot))