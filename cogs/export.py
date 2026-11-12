import io
import csv
import discord
from discord.ext import commands
import database

class DataExport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="exportblacklist", description="Export all globally blacklisted users as a CSV file.")
    @commands.has_permissions(administrator=True)
    async def export_blacklist(self, ctx: commands.Context):
        """Generates and sends a CSV file containing all global blacklist entries."""
        entries = database.get_all_blacklisted_users()

        if not entries:
            await ctx.send("❌ The global blacklist database is currently empty.", ephemeral=True)
            return

        # Create an in-memory string buffer for the CSV data
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Write header and rows
        writer.writerow(["User ID", "Reason", "Added Timestamp (ISO)"])
        for entry in entries:
            writer.writerow([entry.get("user_id"), entry.get("reason"), entry.get("added_at")])

        # Convert string buffer to bytes for discord.File
        buffer.seek(0)
        file_bytes = io.BytesIO(buffer.getvalue().encode("utf-8"))
        file_bytes.seek(0)

        file = discord.File(fp=file_bytes, filename="global_blacklist_backup.csv")

        embed = discord.Embed(
            title="📊 Global Blacklist Export",
            description=f"Successfully exported **{len(entries)}** blacklist record(s).",
            color=discord.Color.green(),
            timestamp=discord.utils.utcnow(),
        )
        
        await ctx.send(embed=embed, file=file)

async def setup(bot):
    await bot.add_cog(DataExport(bot))