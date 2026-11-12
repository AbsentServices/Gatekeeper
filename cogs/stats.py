import time
import discord
from discord.ext import commands

class Stats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.hybrid_command(name="status", description="Check the bot's health, latency, and uptime.")
    async def status(self, ctx: commands.Context):
        """Displays bot telemetry and latency stats."""
        # Calculate uptime
        uptime_seconds = int(time.time() - self.start_time)
        days, remainder = divmod(uptime_seconds, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s" if days > 0 else f"{hours}h {minutes}m {seconds}s"

        latency_ms = round(self.bot.latency * 1000, 2)

        embed = discord.Embed(
            title="🛡️ Gatekeeper Bot Status",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Latency", value=f"`{latency_ms} ms`", inline=True)
        embed.add_field(name="Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="Connected Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="Total Cached Users", value=f"`{sum(g.member_count for g in self.bot.guilds):,}`", inline=True)
        
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Stats(bot))