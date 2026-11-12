import discord
from discord.ext import commands

class Lockdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="lockdown", description="Lock the current channel to prevent members from chatting.")
    @commands.has_permissions(manage_channels=True, administrator=True)
    async def lockdown(self, ctx: commands.Context, channel: discord.TextChannel = None, *, reason: str = "No reason provided"):
        """Locks down a text channel immediately."""
        target_channel = channel or ctx.channel
        default_role = ctx.guild.default_role

        # Check current permissions to avoid redundant updates
        overwrite = target_channel.overwrites_for(default_role)
        if overwrite.send_messages is False:
            await ctx.send(f"⚠️ {target_channel.mention} is already locked down.", ephemeral=True)
            return

        # Disable send_messages for the @everyone role
        overwrite.send_messages = False
        try:
            await target_channel.set_permissions(default_role, overwrite=overwrite, reason=f"Lockdown by {ctx.author}: {reason}")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to modify channel permissions.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🔒 Channel Lockdown Engaged",
            description=f"{target_channel.mention} has been placed under lockdown by staff.",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Reason", value=f"```{reason}```", inline=False)
        embed.set_footer(text=f"Action by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="unlock", description="Unlock a previously locked text channel.")
    @commands.has_permissions(manage_channels=True, administrator=True)
    async def unlock(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Restores standard chatting permissions to a text channel."""
        target_channel = channel or ctx.channel
        default_role = ctx.guild.default_role

        overwrite = target_channel.overwrites_for(default_role)
        # Reset send_messages override back to neutral (None)
        overwrite.send_messages = None
        
        try:
            await target_channel.set_permissions(default_role, overwrite=overwrite, reason=f"Unlock by {ctx.author}")
        except discord.Forbidden:
            await ctx.send("❌ I do not have permission to modify channel permissions.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🔓 Channel Lockdown Lifted",
            description=f"{target_channel.mention} has been restored to normal operation.",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_footer(text=f"Action by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Lockdown(bot))