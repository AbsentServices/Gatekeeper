import discord
from discord.ext import commands
import database

class AuditLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_audit_log(self, guild_id: int, title: str, description: str, color: discord.Color, admin: discord.User):
        """Sends an administrative audit log entry to the guild's log channel."""
        log_channel_id = database.get_log_channel(guild_id)
        if not log_channel_id:
            return

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.get_channel(log_channel_id)
        if not channel:
            return

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=f"Admin: {admin.name} ({admin.id})", icon_url=admin.display_avatar.url)
        embed.set_footer(text="Security Audit Trail")

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        """Listens for successful administrative command executions to record audit logs."""
        if not ctx.guild or not ctx.author.guild_permissions.administrator:
            return

        # Track modifications made via whitelist or blacklist commands
        if ctx.command and ctx.command.qualified_name.startswith(("blacklist", "whitelist")):
            action_name = ctx.command.qualified_name
            args_str = " ".join(str(arg) for arg in ctx.args[2:]) # Extract command arguments safely
            
            await self.send_audit_log(
                guild_id=ctx.guild.id,
                title=f"🛠️ Admin Action: `!{action_name}`",
                description=f"**Executed in:** {ctx.channel.mention}\n**Arguments:** `{args_str or 'None'}`",
                color=discord.Color.gold(),
                admin=ctx.author
            )

async def setup(bot):
    await bot.add_cog(AuditLogger(bot))