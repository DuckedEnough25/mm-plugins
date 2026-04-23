import discord
from discord.ext import commands

from core import checks
from core.models import PermissionLevel

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
            "honeypot_log_channel_id": None,
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
        self.honeypot_log_channel = self.bot.guild.get_channel(self.config["honeypot_log_channel_id"])

    @commands.Cog.listener()
    async def on_message(self, message):
        if not self.config["enabled"]:
            return

        if message.author.bot:
            return

        if not self.config["honeypot_channel_id"]:
            return

        if message.channel.id != self.config["honeypot_channel_id"]:
            return


        if self.honeypot_immune_role in message.author.roles:
            return

        m = None
        try:
            m = await message.author.send(self.config["honeypot_ban_message"].format(server=self.bot.guild.name))
        except discord.Forbidden:
            pass

        await message.delete()
        await self.bot.guild.ban(message.author, reason="Honeypot triggered. User is likely compromised.", delete_message_days=1)
        if not self.honeypot_log_channel:
            self.honeypot_log_channel = await self.bot.guild.fetch_channel(self.config["honeypot_log_channel_id"])
        if m:
            await self.honeypot_log_channel.send(f"User {message.author} ({message.author.id}) was banned for triggering the honeypot. User was successfully sent the ban message.")
        else:
            await self.honeypot_log_channel.send(f"User {message.author} ({message.author.id}) was banned for triggering the honeypot. Failed to send the ban message (DMs likely closed).")

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
        await ctx.send(f"Honeypot immune role set to {role.name}.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @honeypot.command(name="setbanmessage")
    async def set_ban_message(self, ctx, *, message):
        self.config["honeypot_ban_message"] = message
        await self.update_config()
        await ctx.send("Honeypot ban message updated.")

    @checks.has_permissions(PermissionLevel.ADMINISTRATOR)
    @honeypot.command(name="setlogchannel")
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        self.config["honeypot_log_channel_id"] = channel.id
        await self.update_config()
        await ctx.send(f"Honeypot log channel set to {channel.mention}.")

async def setup(bot):
    await bot.add_cog(Honeypot(bot))