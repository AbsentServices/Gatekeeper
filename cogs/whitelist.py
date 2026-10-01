import discord
from discord.ext import commands
import database

class Whitelist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group(name="whitelist", fallback="check")
    @commands.has_permissions(administrator=True)
    async def whitelist(self, ctx: commands.Context, user: discord.User):
        """Check if a user is whitelisted."""
        status = database.is_whitelisted(ctx.guild.id, user.id)
        msg = f"✅ {user.mention} is **whitelisted** in this server." if status else f"❌ {user.mention} is **NOT whitelisted**."
        await ctx.send(msg)

    @whitelist.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add(self, ctx: commands.Context, user: discord.User):
        """Add a user to the server whitelist."""
        success = database.add_to_whitelist(ctx.guild.id, user.id)
        if success:
            await ctx.send(f"✅ Added {user.mention} to the whitelist.")
        else:
            await ctx.send(f"⚠️ Failed to whitelist {user.mention}.")

    @whitelist.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, user: discord.User):
        """Remove a user from the server whitelist."""
        success = database.remove_from_whitelist(ctx.guild.id, user.id)
        if success:
            await ctx.send(f"🗑️ Removed {user.mention} from the whitelist.")
        else:
            await ctx.send(f"⚠️ {user.mention} was not on the whitelist.")

async def setup(bot):
    await bot.add_cog(Whitelist(bot))