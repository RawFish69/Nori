"""Build command group."""

import json

import hikari
import lightbulb
import miru

from lib.build_recipe_utils import build_file_remove, build_file_search, build_file_updater
from lib.config import BOT_PATH, build_data
from lib.permissions import build_contributor_only
from lib.utils import check_user_access

CLASS_ICONS = {
    "Warrior": "<:spear:1330019288165122099>",
    "Mage": "<:wand:1330019445791391744>",
    "Archer": "<:bow:1330019516503167068>",
    "Assassin": "<:dagger:1330019458466713641>",
    "Shaman": "<:relik:1330019531929681920>",
}


def _chunk_results(items, size=10):
    return [items[index:index + size] for index in range(0, len(items), size)]


def _build_embed(page_results, tags, page, total_pages, builds_found):
    tags_text = ", ".join(tags)
    page_line = f"Page **{page}** of **{total_pages}**"
    embed = hikari.Embed(
        title=f"Builds with keyword: __{tags_text}__",
        description=f"**{builds_found}** Results found\n{page_line}",
        color="#8DF7AD",
    )
    for index, build in enumerate(page_results, start=1):
        build_title = list(build.keys())[0]
        build_entry = build[build_title]
        build_tags = build_entry.get("tag", "")
        build_link = build_entry.get("link", "")
        build_credit = build_entry.get("credit", "N/A")
        build_icon = CLASS_ICONS.get(build_entry.get("class", ""), "")
        for tag in tags:
            if tag and tag.lower() in build_tags.lower():
                build_tags = build_tags.replace(tag, f"__{tag}__")
        embed.add_field(
            f"{index}. {build_icon} {build_title}",
            f"[Build Link]({build_link})\n{build_tags}\nCredit: *{build_credit}*",
        )
    web_page = "[Build Search on Nori-Web](https://nori.fish/wynn/build/)"
    embed.add_field(f"[{page}/{total_pages}]", web_page)
    embed.set_footer("Nori Bot - Wynn Builds")
    return embed


def _load_items():
    with open(BOT_PATH / "items.json", "r", encoding="utf-8") as file:
        return json.load(file)


def _item_match(name, item_data):
    data = None
    for item_name in item_data:
        if name.lower() == item_name.lower():
            data = item_data[item_name]
            break

    if not data:
        return None

    icon_id = None
    icon_data = data.get("icon")
    if isinstance(icon_data, dict):
        if icon_data.get("format") == "attribute":
            icon_id = icon_data.get("value", {}).get("name")
        elif icon_data.get("format") == "legacy":
            icon_value = icon_data.get("value")
            icon_id = icon_value.replace(":", "_") if isinstance(icon_value, str) else None

    item_type = data.get("subType")
    type_translate = {
        "spear": "Warrior",
        "wand": "Mage",
        "bow": "Archer",
        "dagger": "Assassin",
        "relik": "Shaman",
    }
    class_type = type_translate.get(item_type, "Unknown")
    icon_link = f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp" if icon_id else None
    return {"icon": icon_link, "class": class_type}


class BuildView(miru.View):
    def __init__(self, user_id: int, timeout: float = 60):
        super().__init__(timeout=timeout)
        self.user_id = user_id

    async def _edit_page(self, ctx: miru.Context, direction: int):
        state = build_data.get(self.user_id)
        if not state:
            await ctx.edit_response("Build search session expired.", components=[])
            self.stop()
            return

        total_pages = len(state["pages"])
        page = state["page"] + direction
        if page < 1:
            page = total_pages
        elif page > total_pages:
            page = 1
        state["page"] = page

        page_results = state["pages"][page - 1]
        embed = _build_embed(page_results, state["tags"], page, total_pages, state["count"])
        await ctx.edit_response(embed=embed)

    @miru.button(emoji="⬅", style=hikari.ButtonStyle.SECONDARY)
    async def button_previous(self, button: miru.Button, ctx: miru.Context):
        await self._edit_page(ctx, -1)

    @miru.button(emoji="➡", style=hikari.ButtonStyle.SECONDARY)
    async def button_next(self, button: miru.Button, ctx: miru.Context):
        await self._edit_page(ctx, 1)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f"Failed to edit message on timeout: {error}")


def load_build_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load build commands."""

    @bot.command()
    @lightbulb.command("build", "Class builds")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def build(ctx: lightbulb.Context):
        pass

    @build.child()
    @lightbulb.option("keyword_3", "3rd Keyword", required=False, default=None)
    @lightbulb.option("keyword_2", "2nd Keyword", required=False, default=None)
    @lightbulb.option("keyword_1", "1st Keyword", required=True)
    @lightbulb.command("search", "Look for specific build with key words")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def build_search(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)

        tag_2 = ctx.options.keyword_2
        tag_3 = ctx.options.keyword_3
        tags = [ctx.options.keyword_1]
        tags.append(tag_2) if tag_2 else None
        tags.append(tag_3) if tag_3 else None
        tags_text = ", ".join(tags)

        result = await build_file_search(tags)
        search_result = result["Result"]
        builds_found = len(search_result)
        if not search_result:
            server_link = "https://discord.gg/tU7eaKAWb2"
            result_embed = hikari.Embed(
                title=f"No result found with tag: __{tags_text}__",
                color="#FF0000",
            )
            result_embed.add_field(
                "Can't find a specific type of build?",
                f"feel free to suggest or request it in the support server\n[Click to join]({server_link})",
            )
            await ctx.respond(embed=result_embed)
            return

        pages = _chunk_results(search_result, 10)
        user_id = ctx.user.id
        build_data[user_id] = {
            "page": 1,
            "pages": pages,
            "count": builds_found,
            "tags": tags,
        }

        embed = _build_embed(pages[0], tags, 1, len(pages), builds_found)
        if len(pages) > 1:
            view = BuildView(user_id=user_id, timeout=60)
            message = await ctx.respond(embed=embed, components=view.build())
            message = await message
            await view.start(message)
            await view.wait()
        else:
            await ctx.respond(embed=embed)

    @build.child()
    @lightbulb.add_checks(build_contributor_only())
    @lightbulb.option("credit", "Build Credit (names)")
    @lightbulb.option("weapon", "Weapon Name (Item)")
    @lightbulb.option("link", "Wynnbuilder Link")
    @lightbulb.option("keywords", "Build Tags (keywords)")
    @lightbulb.option("name", "Name of the Build")
    @lightbulb.command("submit", "Submit Build (Contributor Only)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def build_submit(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)

        item_data = _load_items()
        matched_item = _item_match(ctx.options.weapon, item_data)
        if not matched_item:
            await ctx.respond(f"Cannot find weapon `{ctx.options.weapon}` in item database.")
            return

        build_submission = {
            ctx.options.name: {
                "tag": ctx.options.keywords,
                "link": ctx.options.link,
                "credit": ctx.options.credit,
                "weapon": ctx.options.weapon,
                "icon": matched_item["icon"],
                "class": matched_item["class"],
            }
        }
        await build_file_updater(build_submission)

        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        build_embed = hikari.Embed(
            title="Build Submission",
            description=f"Uploaded by {username}",
            color="#8DF7AD",
        )
        build_embed.add_field(
            f"Title: {ctx.options.name}",
            f"Keywords: {ctx.options.keywords}\n[{ctx.options.name} Build]({ctx.options.link})",
        )
        build_embed.set_footer("Nori Bot - Maintainer Tools")
        await ctx.respond(build_embed)

    @build.child()
    @lightbulb.add_checks(build_contributor_only())
    @lightbulb.option("name", "Name of the Build")
    @lightbulb.command("remove", "Remove Build (Contributor Only)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def build_remove(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        remove_result = await build_file_remove(ctx.options.name)
        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        result = (
            f"Successfully removed {ctx.options.name} from db"
            if remove_result
            else f"Cannot find {ctx.options.name} in db, try another name?"
        )
        build_embed = hikari.Embed(
            title=f"Build deletion by {username}",
            description=result,
            color="#8DF7AD",
        )
        build_embed.set_footer("Nori Bot - Maintainer Tools")
        await ctx.respond(build_embed)

    @build.child()
    @lightbulb.command("help", "Keyword/tag sorted by attributes")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def build_help(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        display_embed = hikari.Embed(
            title="List of tags sorted for build search",
            description="These are examples you may use as a reference",
            color="#8DF7AD",
        )
        display_embed.add_field("Search by class", "warrior, mage, archer, assassin, shaman...")
        display_embed.add_field("Search by archetype", "fallen, boltslinger, arcanist, etc")
        display_embed.add_field("Search by item", "Either type, tier, or name\n")
        display_embed.add_field("Search by content", "raid, lootrun, war, leveling, etc")
        display_embed.add_field("Search by play style", "tank, dps, mobility, etc")
        display_embed.add_field("Search by misc", "no-mythic, rage, no-tome, etc")
        display_embed.set_footer("Nori Bot - Search Tags")
        await ctx.respond(embed=display_embed)

