import math
import discord
from discord.ext import commands
import database


class BlacklistConfirmView(discord.ui.View):
    """Interactive confirmation prompt for sensitive blacklist additions or removals."""

    def __init__(self, author_id: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.value: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ You cannot interact with this confirmation prompt.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Confirm Action", style=discord.ButtonStyle.danger, custom_id="confirm_blacklist")
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, custom_id="cancel_blacklist")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self):
        self.value = False
        for child in self.children:
            child.disabled = True


class BlacklistPaginator(discord.ui.View):
    """Interactive Discord UI View providing page navigation for blacklisted users."""

    def __init__(self, author_id: int, entries: list[dict], per_page: int = 5):
        super().__init__(timeout=180)
        self.author_id = author_id
        self.entries = entries
        self.per_page = per_page
        self.current_page = 0
        self.max_pages = max(1, math.ceil(len(entries) / per_page))
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page >= self.max_pages - 1

    def create_embed(self) -> discord.Embed:
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
        for entry in self.entries[start_idx:end_idx]:
            user_id = entry["user_id"]
            reason = entry.get("reason", "No reason provided")
            embed.add_field(
                name=f"User ID: `{user_id}`",
                value=f"**Reason:** {reason}\n**Mention:** <@{user_id}>",
                inline=False,
            )
        embed.set_footer(text=f"Page {self.current_page + 1}/{self.max_pages} • Total: {len(self.entries)}")
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("❌ You cannot control this menu.", ephemeral=True)
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


class Blacklist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_kick_log(self, guild: discord.Guild, member: discord.Member, reason: str):
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
        embed.add_field(name="Blacklist Reason", value=f"```{reason}```", inline=False)
        
        try:
            await channel.send(embed=embed)
        except discord.Forbidden:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Auto-kick members on join if blacklisted, verifying guild whitelists first."""
        if database.is_globally_blacklisted(member.id):
            if database.is_whitelisted(member.guild.id, member.id):
                return  # Bypass kick if whitelisted

            reason = database.get_blacklist_reason(member.id)
            try:
                await member.send(
                    f"You are globally blacklisted across servers running **{self.bot.user.name}**.\n**Reason:** {reason}"
                )
            except discord.Forbidden:
                pass

            try:
                await member.kick(reason=f"Global Network Blacklist: {reason}")
                await self.send_kick_log(member.guild, member, reason)
            except discord.Forbidden:
                pass

    @commands.hybrid_group(name="blacklist", fallback="check")
    async def blacklist(self, ctx: commands.Context, user: discord.User):
        """Check if a user is globally blacklisted."""
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
        view.message = message

    @blacklist.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add(self, ctx: commands.Context, user: discord.User, *, reason: str = "No reason provided"):
        """Add a user to the GLOBAL network blacklist with interactive confirmation."""
        if database.is_globally_blacklisted(user.id):
            await ctx.send(f"⚠️ {user.mention} is already on the global blacklist.", ephemeral=True)
            return

        view = BlacklistConfirmView(author_id=ctx.author.id)
        prompt_msg = await ctx.send(
            f"⚠️ **Confirmation Required:** Are you sure you want to **globally blacklist** {user.mention} across all connected servers?\n**Reason:** *{reason}*",
            view=view
        )

        await view.wait()
        if not view.value:
            await prompt_msg.edit(content="❌ Blacklist action cancelled.", view=None)
            return

        success = database.add_to_global_blacklist(user_id=user.id, reason=reason, admin_id=ctx.author.id)
        if success:
            await prompt_msg.edit(
                content=f"🌐 **Global Blacklist Updated:** {user.mention} was blacklisted across all servers.\n**Reason:** *{reason}*",
                view=None
            )

            # Kick user across connected guilds
            for guild in self.bot.guilds:
                member = guild.get_member(user.id)
                if member and not database.is_whitelisted(guild.id, user.id):
                    try:
                        await member.kick(reason=f"Global Blacklist: {reason}")
                        await self.send_kick_log(guild, member, reason)
                    except discord.Forbidden:
                        pass
        else:
            await prompt_msg.edit(content=f"⚠️ Failed to add {user.mention} to the global blacklist.", view=None)

    @blacklist.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx: commands.Context, user: discord.User):
        """Remove a user from the global network blacklist with interactive confirmation."""
        if not database.is_globally_blacklisted(user.id):
            await ctx.send(f"⚠️ {user.mention} is not currently on the global blacklist.", ephemeral=True)
            return

        view = BlacklistConfirmView(author_id=ctx.author.id)
        prompt_msg = await ctx.send(
            f"⚠️ **Confirmation Required:** Are you sure you want to remove {user.mention} from the **global blacklist**?",
            view=view
        )

        await view.wait()
        if not view.value:
            await prompt_msg.edit(content="❌ Removal action cancelled.", view=None)
            return

        success = database.remove_from_global_blacklist(user.id)
        if success:
            await prompt_msg.edit(content=f"✅ Successfully removed {user.mention} from the global blacklist.", view=None)
        else:
            await prompt_msg.edit(content=f"⚠️ Failed to remove {user.mention} from the global blacklist.", view=None)


async def setup(bot):
    await bot.add_cog(Blacklist(bot))