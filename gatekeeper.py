import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

# Setup Intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Required for tracking user joins and member checks

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} application/slash commands.")
    except Exception as e:
        print(f"Failed to sync slash commands: {e}")

async def load_extensions():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")
            print(f"Loaded Cog: {filename[:-3]}")

async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

# Add this event listener inside gatekeeper.py alongside your on_ready event

@bot.event
async def on_command_error(ctx: commands.Context, error: Exception):
    """Global error handler to catch command failures gracefully."""
    # Unwrap original errors if wrapped by command invocation
    error = getattr(error, "original", error)

    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You do not have the required administrator permissions to run this command.", ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing required argument: `{error.param.name}`. Check command usage.", ephemeral=True)
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid input format provided. Please double-check your arguments.", ephemeral=True)
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Slow down! Try again in `{error.retry_after:.1f}` seconds.", ephemeral=True)
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You are not authorized to execute this command.", ephemeral=True)
    else:
        # Log unexpected errors to console for debugging
        print(f"Ignoring unhandled command error in {ctx.command}: {error}")
        await ctx.send("❌ An unexpected error occurred. Please try again later.", ephemeral=True)