import math
import discord
from discord.ext import commands
import database


class BlacklistPaginator(discord.ui.View):
    """Interactive Discord UI View providing page navigation for blacklisted users."""

    def __init__(self, author_id: int, entries: list[dict], per_page: int = 5):
        super().__init__(timeout=180)  # Controls automatically disable after 3 minutes
        self.author_id = author_id
        self.entries = entries
        self.per_page = per_page
        self.current_page = 0
        self.max_pages = max(1, math.ceil(len(entries) / per_page))

        self.update_buttons()

    def update_buttons(self):
        """Enable or disable navigation buttons based on current page index."""
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.max_pages - 1

    def create_embed(self) -> discord.Embed:
        """Constructs an embed for the active page."""
        embed = discord.Embed(
            title="⛔ Global Blacklist Directory",
            color=discord.Color.dark_red(),
            timestamp=discord.utils.utcnow(),
        )

        if not self.entries:
            embed.description = "No users are currently on the global blacklist."
            embed.set_footer(text="Page 0/0 • Global Security")
            return embed

        start_idx = self.current_page * self.per_page
        end_idx = start_idx + self.per_page
        page_entries = self.entries[start_idx:end_idx]

        for entry in page_entries:
            user_id = entry["user_id"]
            reason = entry.get("reason", "No reason provided")
            added_at = entry.get("added_at", "")

            # Format timestamp if ISO string exists
            timestamp_str = ""
            if added_at:
                try:
                    dt = discord.utils.parse_time(added_at)
                    timestamp_str = f" | Added <t:{int(dt.timestamp())}:R>"
                except Exception:
                    pass

            embed.add_field(
                name=f"User ID: `{user_id}`",
                value=f"**Reason:** {reason}{timestamp_str}\n**Mention:** <@{user_id}>",
                inline=False,
            )

        embed.set_footer(
            text=f"Page {self.current_page + 1}/{self.max_pages} • Total Blacklisted: {len(self.entries)}"
        )
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """Ensure only the command invoker can use the navigation buttons."""
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "❌ You cannot control this menu.", ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.primary, custom_id="prev_page")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary, custom_id="next_page")
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.create_embed(), view=self)

    async def on_timeout(self):
        """Disable all buttons when the view times out."""
        for item in self.children:
            item.disabled = True
        # Try to edit message if context permits
        try:
            if hasattr(self, "message") and self.message:
                await self.message.edit(view=self)
        except Exception:
            pass


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_kick_log(self, guild: discord.Guild, member: discord.Member, reason: str):
        """Helper method to send a structured embed log when a blacklisted user is kicked."""
        log_channel_id = database.get_log_channel(guild.id)
        if not log_channel_id:
            return

        channel = guild.get_channel(log_channel_id)
        if not channel:
            return

        embed = discord.Embed(
            title="⛔ Blacklisted User Intercepted",
            description=f"A globally blacklisted user attempted to join **{guild.name}** and was automatically removed.",
            color=discord.Color.red(),
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(name=f"{member.name} ({member.id})", icon_url=member.display_avatar.url)
        embed.add_field(name="User Mention", value=member.mention, inline=True)
        embed.add_field(name="Account Created", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
        embed.add_field(name="Blacklist Reason", value=f"```{reason}```", inline=False)
        embed.set_footer(text="Global Security Logging", icon_url=self.bot.user.display_avatar.url)

        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.hybrid_group(name="blacklist", fallback="check")
    async def blacklist(self, ctx: commands.Context, user: discord.User):
        """Check if a user is globally blacklisted across all servers."""
        is_banned = database.is_globally_blacklisted(user.id)
        if is_banned:
            reason = database.get_blacklist_reason(user.id)
            await ctx.send(f"⛔ {user.mention} is **GLOBALLY blacklisted**!\n**Reason:** {reason}")
        else:
            await ctx.send(f"✅ {user.mention} is not globally blacklisted.")

    @blacklist.command(name="list")
    @commands.has_permissions(administrator=True)
    async def list_blacklisted(self, ctx: commands.Context):
        """Displays an interactive paginated list of all globally blacklisted users."""
        entries = database.get_all_blacklisted_users()

        if not entries:
            await ctx.send("✅ The global blacklist is currently empty.")
            return

        view = BlacklistPaginator(author_id=ctx.author.id, entries=entries, per_page=5)
        embed = view.create_embed()
        
        message = await ctx.send(embed=embed, view=view)
        view.message = message  # Save message reference for timeout disabling

    @blacklist.command(name="setlogchannel")
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the log channel where auto-kick notifications will be posted."""
        success = database.set_log_channel(ctx.guild.id, channel.id)
        if success:
            await ctx.send(f"✅ Logging channel set to {channel.mention}.")
        else:
            await ctx.send("⚠️️ Failed to update log channel setting.")

    @blacklist.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add(self, ctx: commands.Context, user: discord.User, *, reason: str = "No reason provided"):
        """Add a user to the GLOBAL network blacklist (Kicks them from all bot servers)."""
        success = database.add_to_global_blacklist(user_id=user.id, reason=reason, admin_id=ctx.author.id)

        if success:
            await ctx.send(
                f"🌐 **Global Blacklist Updated:** {user.mention} was blacklisted across all servers.\n**Reason:** *{reason}*"
            )

            kicked_guilds = 0
            for guild in self.bot.guilds:
                member = guild.get_member(user.id)
                if member:
                    try:
                        await member.send(
                            f"You have been globally blacklisted from all servers using {self.bot.user.name}.\nReason: {reason}"
                        )
                    except discord.Forbidden:
                        pass

                    try:
                        await member.kick(reason=f"Global Blacklist: {reason}")
                        kicked_guilds += 1
                        await self.send_kick_log(guild, member, reason)
                    except discord.Forbidden:
                        pass

            if kicked_guilds > 0:
                await ctx.send(f"🧹 Automatically kicked {user.mention} from **{kicked_guilds}** server(s).")
        else:
            await ctx.send(f"⚠️ Failed to add {user.mention} to the global blacklist.")

    @blacklist.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, user: discord.User):
        """Remove a user from the global network blacklist."""
        success = database.remove_from_global_blacklist(user.id)
        if success:
            await ctx.send(f"✅ Removed {user.mention} from the global blacklist.")
        else:
            await ctx.send(f"⚠️ {user.mention} was not globally blacklisted.")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Auto-kick members on join if blacklisted, and dispatch an embed log."""
        if database.is_globally_blacklisted(member.id):
            reason = database.get_blacklist_reason(member.id)

            try:
                await member.send(
                    f"You are globally blacklisted across all servers running **{self.bot.user.name}**.\n"
                    f"**Reason:** {reason}"
                )
            except discord.Forbidden:
                pass

            try:
                await member.kick(reason=f"Global Network Blacklist: {reason}")
                await self.send_kick_log(member.guild, member, reason)
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(Blacklist(bot))