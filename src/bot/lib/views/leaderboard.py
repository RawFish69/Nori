"""Interactive leaderboard views for modular nori_bot."""

import hikari
import miru

import lib.config as config
from lib.leaderboard_utils import profession_leaderboard, raid_leaderboard, stat_leaderboard
from lib.utils import format_compact

RAID_VIEW_TYPES = {
    "TNA": ("tna", "The Nameless Anomaly", "Clears", False),
    "TCC": ("tcc", "The Canyon Colossus", "Clears", False),
    "NOL": ("nol", "Nexus of Light", "Clears", False),
    "NOG": ("nog", "Nest of the Grootslangs", "Clears", False),
    "TWP": ("twp", "The Wartorn Palace", "Clears", False),
    "ALL": ("all", "All Raids", "Clears", False),
    "RDD": ("damage_dealt", "Raid Damage Dealt", "Dmg Dealt", True),
    "RDT": ("damage_taken", "Raid Damage Taken", "Dmg Taken", True),
    "RHL": ("heal", "Raid Healing", "Heal", True),
    "RDX": ("deaths", "Raid Deaths", "Deaths", True),
    "RBT": ("buffs_taken", "Raid Buffs Taken", "Buffs", True),
    "RGU": ("gambits_used", "Raid Gambits Used", "Gambits", True),
}

STAT_VIEW_TYPES = {
    "Chest": ("Chest", "Opened"),
    "Mob": ("Mob", "Kills"),
    "War": ("War", "Total"),
    "Dungeon": ("Dungeon", "Clears"),
    "Playtime": ("Playtime", "Hours"),
    "PvP": ("PvP", "Kills"),
    "Quests": ("Quests", "Total"),
    "Levels": ("Levels", "Total"),
}

PROFESSION_OPTIONS = [
    ("Woodcutting", "Woodcutting"),
    ("Mining", "Mining"),
    ("Fishing", "Fishing"),
    ("Farming", "Farming"),
    ("Scribing", "Scribing"),
    ("Alchemism", "Alchemism"),
    ("Cooking", "Cooking"),
    ("Jeweling", "Jeweling"),
    ("Tailoring", "Tailoring"),
    ("Armouring", "Armouring"),
    ("Weaponsmithing", "Weaponsmithing"),
    ("Woodworking", "Woodworking"),
]


class _BaseView(miru.View):
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if hasattr(self, "message") and self.message is not None:
                await self.message.edit(components=self.build())
        except Exception as error:
            print(f"view timeout update failed: {error}")


def _table_display(entries: list, page_num: int, value_header: str, *, compact_values: bool = False) -> str:
    top_entries = entries[(page_num - 1) * 10: page_num * 10]
    if not top_entries:
        top_entries = entries[:10]

    formatted_values = []
    for entry in top_entries:
        if not entry:
            formatted_values.append("0")
            continue
        raw_value = list(entry.values())[0]
        formatted_values.append(format_compact(raw_value) if compact_values else str(int(raw_value)))
    max_name_length = max([len(list(entry.keys())[0]) for entry in top_entries if entry] + [6])
    max_value_length = max([len(value) for value in formatted_values] + [len(value_header)])
    border_line = "+-----+" + "-" * (max_name_length + 2) + "+" + "-" * (max_value_length + 2) + "+\n"

    display = "```json\n"
    display += border_line
    display += f"| {'#':^3} | {'Player':<{max_name_length}} | {value_header:>{max_value_length}} |\n"
    display += border_line
    for index, entry in enumerate(top_entries):
        if not entry:
            continue
        name = list(entry.keys())[0]
        value = formatted_values[index]
        display += (
            f"| {(page_num - 1) * 10 + (index + 1):3d} | "
            f"{name:<{max_name_length}} | {value:>{max_value_length}} |\n"
        )
    display += border_line + "```"
    return display


class raidView(_BaseView):
    @miru.button(label="TNA", style=hikari.ButtonStyle.PRIMARY, row=0)
    async def button_tna(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "TNA")

    @miru.button(label="TCC", style=hikari.ButtonStyle.PRIMARY, row=0)
    async def button_tcc(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "TCC")

    @miru.button(label="NoL", style=hikari.ButtonStyle.PRIMARY, row=0)
    async def button_nol(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "NOL")

    @miru.button(label="NoG", style=hikari.ButtonStyle.PRIMARY, row=0)
    async def button_nog(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "NOG")

    @miru.button(label="TWP", style=hikari.ButtonStyle.PRIMARY, row=0)
    async def button_twp(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "TWP")

    @miru.button(label="All", style=hikari.ButtonStyle.SUCCESS, row=1)
    async def button_all(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "ALL")

    @miru.button(label="Dmg+", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_damage_dealt(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "RDD")

    @miru.button(label="Dmg-", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_damage_taken(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "RDT")

    @miru.button(label="Heal", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_heal(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "RHL")

    @miru.button(label="Deaths", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_deaths(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "RDX")

    @miru.button(label="Buffs", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_buffs(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "RBT")

    @miru.button(label="Gambits", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_gambits(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "RGU")

    async def _select_type(self, ctx: miru.ViewContext, type_key: str):
        meta = RAID_VIEW_TYPES.get(type_key)
        label = meta[1] if meta else type_key
        await ctx.edit_response(embed=hikari.Embed(title=f"Processing {label} Leaderboard", color="#AEB1B1"))
        config.lb_user_cache.setdefault(ctx.user.username, {"type": "", "page": 1})
        config.lb_user_cache[ctx.user.username]["type"] = type_key
        config.lb_user_cache[ctx.user.username]["page"] = 1
        await self.lb_display(ctx, 1, type_key)

    async def lb_display(self, ctx: miru.ViewContext, page_num: int, raid_type: str):
        meta = RAID_VIEW_TYPES.get(raid_type)
        if meta is None:
            await ctx.respond("Unknown raid leaderboard type.", flags=hikari.MessageFlag.EPHEMERAL)
            return
        lookup_key, embed_label, value_header, is_metric = meta
        ranking_data = await raid_leaderboard(lookup_key) or []
        if not ranking_data:
            empty_embed = hikari.Embed(
                title=f"{embed_label} Leaderboard",
                description="No data yet - Wynncraft has not backfilled this metric for ranked players.",
                color="#5078FF",
            )
            await ctx.edit_response(embed=empty_embed)
            return

        display = _table_display(ranking_data, page_num, value_header, compact_values=is_metric)
        raid_embed = hikari.Embed(
            title="Wynncraft Raid Report",
            description="The leaderboard player data updates every hour; changed-ign reconciliation runs every 12h.",
            color="#5078FF",
        )
        raid_embed.add_field(f"{embed_label} Leaderboard", display)
        raid_embed.set_footer("Nori Bot - Wynn Raid Report")
        await ctx.edit_response(embed=raid_embed)

    @miru.button(label="<<", style=hikari.ButtonStyle.SECONDARY, row=3)
    async def button_first_page(self, ctx: miru.ViewContext, button: miru.Button):
        await self._change_page(ctx, "first")

    @miru.button(label="<", style=hikari.ButtonStyle.SECONDARY, row=3)
    async def button_prev_page(self, ctx: miru.ViewContext, button: miru.Button):
        await self._change_page(ctx, "prev")

    @miru.button(label="menu", style=hikari.ButtonStyle.SUCCESS, row=3)
    async def button_menu(self, ctx: miru.ViewContext, button: miru.Button):
        msg = "```json\n"
        msg += "1. TNA - The Nameless Anomaly\n"
        msg += "2. TCC - The Canyon Colossus\n"
        msg += "3. NoL - Nexus of Light\n"
        msg += "4. NoG - Nest of the Grootslangs\n"
        msg += "5. TWP - The Wartorn Palace\n"
        msg += "6. All - Total raid clears across the five raids\n\n"
        msg += "Aggregate raid metrics (sum across all raids):\n"
        msg += "  Dmg+   - Damage dealt\n"
        msg += "  Dmg-   - Damage taken\n"
        msg += "  Heal   - Healing done\n"
        msg += "  Deaths - Deaths\n"
        msg += "  Buffs  - Buffs taken\n"
        msg += "  Gambits- Gambits used\n```"
        raid_embed = hikari.Embed(
            title="Wynncraft Raid Leaderboard",
            description="Pick a raid clear category or an aggregate metric",
            color="#93FEFD",
        )
        raid_embed.add_field("Information:", msg)
        raid_embed.set_thumbnail("https://cdn.wynncraft.com/nextgen/wynncraft_icon.png")
        raid_embed.set_footer("Nori Bot - Wynn Raid Report")
        await ctx.edit_response(embed=raid_embed)

    @miru.button(label=">", style=hikari.ButtonStyle.SECONDARY, row=3)
    async def button_next_page(self, ctx: miru.ViewContext, button: miru.Button):
        await self._change_page(ctx, "next")

    @miru.button(label=">>", style=hikari.ButtonStyle.SECONDARY, row=3)
    async def button_last_page(self, ctx: miru.ViewContext, button: miru.Button):
        await self._change_page(ctx, "last")

    async def _change_page(self, ctx: miru.ViewContext, action: str):
        state = config.lb_user_cache.setdefault(ctx.user.username, {"type": "", "page": 1})
        if not state.get("type"):
            await ctx.respond("Pick a raid type or Do `/lb raid` first", flags=hikari.MessageFlag.EPHEMERAL)
            return
        page = state.get("page", 1)
        if action == "first":
            page = 1
        elif action == "prev":
            if page <= 1:
                await ctx.respond("This is the first page.", flags=hikari.MessageFlag.EPHEMERAL)
                return
            page -= 1
        elif action == "next":
            if page >= 10:
                await ctx.respond("This is the last page.", flags=hikari.MessageFlag.EPHEMERAL)
                return
            page += 1
        elif action == "last":
            page = 10
        state["page"] = page
        await self.lb_display(ctx, page, state["type"])


class GuildLeaderboardView(_BaseView):
    def __init__(self, user_id: int, timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.user_id = user_id

    @miru.text_select(
        placeholder="Choose leaderboard category...",
        options=[
            miru.SelectOption(label="Raids Total", value="raids_total"),
            miru.SelectOption(label="TNA", value="tna"),
            miru.SelectOption(label="TCC", value="tcc"),
            miru.SelectOption(label="NOL", value="nol"),
            miru.SelectOption(label="NOG", value="nog"),
            miru.SelectOption(label="TWP", value="twp"),
            miru.SelectOption(label="Dungeons", value="dungeons"),
            miru.SelectOption(label="Chests", value="chests"),
            miru.SelectOption(label="Mobs", value="mobs"),
            miru.SelectOption(label="Playtime", value="playtime"),
            miru.SelectOption(label="Quests", value="quests"),
            miru.SelectOption(label="Levels", value="levels"),
        ],
    )
    async def select_callback(self, ctx: miru.ViewContext, select: miru.TextSelect):
        config.user_lb_in_guild[self.user_id]["category"] = select.values[0]
        config.user_lb_in_guild[self.user_id]["page"] = 0
        await self.display_leaderboard(ctx)

    async def display_leaderboard(self, ctx: miru.ViewContext):
        user_data = config.user_lb_in_guild.get(self.user_id, {})
        guild_prefix = user_data.get("guild_prefix")
        category = user_data.get("category")
        page = user_data.get("page", 0)

        if guild_prefix not in config.lb_in_guild:
            await ctx.respond(f"No leaderboard data found for guild `{guild_prefix}`.", flags=hikari.MessageFlag.EPHEMERAL)
            return
        guild_leaderboard = config.lb_in_guild[guild_prefix].get(category, [])
        if not guild_leaderboard:
            await ctx.respond(f"No data available for `{category}` in guild `{guild_prefix}`.", flags=hikari.MessageFlag.EPHEMERAL)
            return

        total_items = len(guild_leaderboard)
        total_pages = max((total_items + 9) // 10, 1)
        page = max(0, min(page, total_pages - 1))
        config.user_lb_in_guild[self.user_id]["page"] = page
        rows = guild_leaderboard[page * 10: min(page * 10 + 10, total_items)]

        compact_categories = {"chests", "mobs", "playtime"}
        rank_width = 4
        ign_width = 24
        stat_width = 14
        formatted_rows = []
        for index, entry in enumerate(rows, start=page * 10 + 1):
            ign, stat = list(entry.items())[0]
            display_stat = format_compact(stat) if category in compact_categories else str(stat)
            formatted_rows.append(
                f"{str(index).rjust(rank_width)} | {ign[:ign_width].ljust(ign_width)} | {display_stat.rjust(stat_width)}"
            )

        header = f"{'#'.rjust(rank_width)} | {'IGN'.ljust(ign_width)} | {'Stat'.rjust(stat_width)}"
        separator = "-" * (rank_width + 3 + ign_width + 3 + stat_width)
        leaderboard_display = "\n".join([header, separator, *formatted_rows])
        embed = hikari.Embed(
            title=f"{category.capitalize()} Leaderboard for {guild_prefix}",
            description=f"```json\n{leaderboard_display}\n```",
            color="#4FE5F9",
        )
        embed.set_footer(text=f"Page {page + 1}/{total_pages}")
        await ctx.edit_response(embed=embed, components=self.build())

    @miru.button(label="◀", style=hikari.ButtonStyle.SECONDARY)
    async def previous_page(self, ctx: miru.ViewContext, button: miru.Button):
        config.user_lb_in_guild[self.user_id]["page"] = max(0, config.user_lb_in_guild[self.user_id]["page"] - 1)
        await self.display_leaderboard(ctx)

    @miru.button(label="▶", style=hikari.ButtonStyle.SECONDARY)
    async def next_page(self, ctx: miru.ViewContext, button: miru.Button):
        config.user_lb_in_guild[self.user_id]["page"] += 1
        await self.display_leaderboard(ctx)


class statView(_BaseView):
    @miru.button(label="Chest", style=hikari.ButtonStyle.SECONDARY)
    async def button_chest(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "Chest")

    @miru.button(label="Mob", style=hikari.ButtonStyle.SECONDARY)
    async def button_mob(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "Mob")

    @miru.button(label="War", style=hikari.ButtonStyle.SECONDARY)
    async def button_war(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "War")

    @miru.button(label="Dungeon", style=hikari.ButtonStyle.SECONDARY)
    async def button_dungeon(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "Dungeon")

    @miru.button(label="Playtime", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_playtime(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "Playtime")

    @miru.button(label="PvP", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_pvp(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "PvP")

    @miru.button(label="Quest", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_quests(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "Quests")

    @miru.button(label="Level", style=hikari.ButtonStyle.SECONDARY, row=1)
    async def button_levels(self, ctx: miru.ViewContext, button: miru.Button):
        await self._select_type(ctx, "Levels")

    async def _select_type(self, ctx: miru.ViewContext, stat_type: str):
        await ctx.edit_response(embed=hikari.Embed(title=f"Processing {stat_type} Leaderboard\nPlease be patient", color="#AEB1B1"))
        config.lb_user_cache.setdefault(ctx.user.username, {"type": "", "page": 1})
        config.lb_user_cache[ctx.user.username]["type"] = stat_type
        config.lb_user_cache[ctx.user.username]["page"] = 1
        await self.lb_display(ctx, 1, stat_type)

    async def lb_display(self, ctx: miru.ViewContext, page_num: int, stat_type: str):
        ranking_data = await stat_leaderboard(stat_type) or []
        if not ranking_data:
            await ctx.respond(f"No data available for `{stat_type}`.", flags=hikari.MessageFlag.EPHEMERAL)
            return
        value_header = STAT_VIEW_TYPES.get(stat_type, (stat_type, "Total"))[1]
        display = _table_display(ranking_data, page_num, value_header)
        stat_embed = hikari.Embed(
            title="Wynncraft Stats Leaderboard",
            description="The leaderboard player data updates every hour; changed-ign reconciliation runs every 12h.",
            color="#D78CFF",
        )
        stat_embed.add_field(f"{stat_type} Leaderboard", display)
        stat_embed.set_footer("Nori Bot - Wynn Stats Leaderboard")
        await ctx.edit_response(embed=stat_embed)

    @miru.button(label="<<", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_first_page(self, ctx: miru.ViewContext, button: miru.Button):
        await self._change_page(ctx, "first")

    @miru.button(label="<", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_prev_page(self, ctx: miru.ViewContext, button: miru.Button):
        await self._change_page(ctx, "prev")

    @miru.button(label="menu", style=hikari.ButtonStyle.SUCCESS, row=2)
    async def button_menu(self, ctx: miru.ViewContext, button: miru.Button):
        msg = "```json\n"
        msg += "1. Chest Opened\n"
        msg += "2. Mobs Killed\n"
        msg += "3. Wars Completed\n"
        msg += "4. Dungeon Clears\n"
        msg += "5. Playtime\n"
        msg += "6. PvP Kills\n"
        msg += "7. Quests Completed\n"
        msg += "8. Total Levels\n```"
        stat_embed = hikari.Embed(title="Wynncraft Leaderboard", description="Select a leaderboard category", color="#93FEFD")
        stat_embed.add_field("Information:", msg)
        stat_embed.set_thumbnail("https://cdn.wynncraft.com/nextgen/wynncraft_icon.png")
        stat_embed.set_footer("Nori Bot - Wynn Stats Leaderboard")
        await ctx.edit_response(embed=stat_embed)

    @miru.button(label=">", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_next_page(self, ctx: miru.ViewContext, button: miru.Button):
        await self._change_page(ctx, "next")

    @miru.button(label=">>", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_last_page(self, ctx: miru.ViewContext, button: miru.Button):
        await self._change_page(ctx, "last")

    async def _change_page(self, ctx: miru.ViewContext, action: str):
        state = config.lb_user_cache.setdefault(ctx.user.username, {"type": "", "page": 1})
        if not state.get("type"):
            await ctx.respond("Pick a stat type or Do `/lb stat` first", flags=hikari.MessageFlag.EPHEMERAL)
            return
        page = state.get("page", 1)
        if action == "first":
            page = 1
        elif action == "prev":
            if page <= 1:
                await ctx.respond("This is the first page.", flags=hikari.MessageFlag.EPHEMERAL)
                return
            page -= 1
        elif action == "next":
            if page >= 10:
                await ctx.respond("This is the last page.", flags=hikari.MessageFlag.EPHEMERAL)
                return
            page += 1
        elif action == "last":
            page = 10
        state["page"] = page
        await self.lb_display(ctx, page, state["type"])


class prof_view(_BaseView):
    @miru.text_select(
        placeholder="Choose profession...",
        options=[miru.SelectOption(label=label, value=value) for label, value in PROFESSION_OPTIONS],
    )
    async def select_callback(self, ctx: miru.ViewContext, select: miru.TextSelect):
        prof_ranking = await profession_leaderboard(select.values[0])
        await ctx.edit_response(prof_ranking)
