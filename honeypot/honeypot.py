import discord
from discord.ext import commands

from core import checks

class Honeypot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.api.get_plugin_partition(self)
        self.config = None
        self.default_config = {
            "enabled": False,
            "honeypot_channel_id": None,
            "honeypot_immune_role_id": None,
            "honeypot_ban_message": "You have been banned from {server} because your account appears to be hijacked. If you believe this is a mistake, please contact support.",
        }
        self.honeypot_immune_role = None

    async def cog_load(self):
        self.config = await self.db.find_one({"_id": "honeypot"})
        if not self.config:
            self.config = self.default_config
            await self.update_config()

    async def update_config(self):
        await self.db.find_one_and_update(
            {"_id": "honeypot"},
            {"$set": self.config},
            upsert=True,
        )
        self.honeypot_immune_role = self.bot.guild.get_role(self.config["honeypot_immune_role_id"])

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.config["enabled"]:
            return

        if message.author.bot:
            return

        if not self.config["honeypot_channel_id"] or not self.config["honeypot_role_id"]:
            return

        if message.channel.id != self.config["honeypot_channel_id"]:
            return


        if self.honeypot_immune_role in message.author.roles:
            return

        try:
            await self.bot.guild.ban(message.author, reason=self.config["honeypot_ban_message"].format(server=self.bot.guild.name), delete_message_days=1)
            await message.delete()
        except discord.Forbidden:
            pass

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @commands.group(name="honeypot", invoke_without_command=True)
    async def honeypot(self, ctx):
        """Advanced menu settings."""
        await ctx.send_help(ctx.command)

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @honeypot.command(name="toggle")
    async def toggle(self, ctx):
        self.config["enabled"] = not self.config["enabled"]
        await self.update_config()
        await ctx.send(f"Honeypot is now {'enabled' if self.config['enabled'] else 'disabled'}.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @honeypot.command(name="setchannel")
    async def set_channel(self, ctx, channel: discord.TextChannel):
        self.config["honeypot_channel_id"] = channel.id
        await self.update_config()
        await ctx.send(f"Honeypot channel set to {channel.mention}.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @honeypot.command(name="setimmune")
    async def set_immune_role(self, ctx, role: discord.Role):
        self.config["honeypot_immune_role_id"] = role.id
        await self.update_config()
        await ctx.send(f"Honeypot immune role set to {role.mention}.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @honeypot.command(name="setbanmessage")
    async def set_ban_message(self, ctx, *, message):
        self.config["honeypot_ban_message"] = message
        await self.update_config()
        await ctx.send("Honeypot ban message updated.")

async def setup(bot):
    await bot.add_cog(Honeypot(bot))