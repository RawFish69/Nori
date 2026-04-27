"""Owner-only operational commands."""

import asyncio
from pathlib import Path

import hikari
import lightbulb
import miru

import lib.config as config
from lib.utils import check_user_access


class LocalCurveSelect(miru.TextSelect):
    async def callback(self, ctx: miru.ViewContext):
        selection = self.values[0]
        config.local_curve_data["user"] = selection
        user_data = config.local_curve_data.get(selection, {})
        file_name = user_data.get("File")
        if file_name:
            file_path = config.USER_IMG_PATH / file_name
            if file_path.exists():
                await ctx.edit_response(content=f"Data loaded for `{selection}`", attachment=hikari.files.File(str(file_path)))
                return
        await ctx.edit_response(content=f"Data loaded for `{selection}`")


class GraphButton(miru.Button):
    def __init__(self):
        super().__init__(style=hikari.ButtonStyle.SUCCESS, label="Graph")

    async def callback(self, ctx: miru.ViewContext):
        username = config.local_curve_data.get("user")
        user_data = config.local_curve_data.get(username, {})
        file_name = user_data.get("File")
        if not file_name:
            await ctx.respond("No graph file available for selected user.", flags=hikari.MessageFlag.EPHEMERAL)
            return
        file_path = config.USER_IMG_PATH / file_name
        if not file_path.exists():
            await ctx.respond(f"Graph file missing: `{file_path}`", flags=hikari.MessageFlag.EPHEMERAL)
            return
        await ctx.edit_response(attachment=hikari.files.File(str(file_path)))


class SplineButton(miru.Button):
    def __init__(self):
        super().__init__(style=hikari.ButtonStyle.PRIMARY, label="Spline")

    async def callback(self, ctx: miru.ViewContext):
        username = config.local_curve_data.get("user")
        spline = config.local_curve_data.get(username, {}).get("Spline")
        if not spline:
            await ctx.respond("No spline data available for selected user.", flags=hikari.MessageFlag.EPHEMERAL)
            return
        await ctx.edit_response(f"Spline Curve:\n`{spline}`")


class RegressionButton(miru.Button):
    def __init__(self):
        super().__init__(style=hikari.ButtonStyle.PRIMARY, label="Regression")

    async def callback(self, ctx: miru.ViewContext):
        username = config.local_curve_data.get("user")
        regression = config.local_curve_data.get(username, {}).get("Regression")
        if not regression:
            await ctx.respond("No regression data available for selected user.", flags=hikari.MessageFlag.EPHEMERAL)
            return
        await ctx.edit_response(f"Regression Curve:\n`{regression}`")


def load_owner_tools_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load owner/admin operation commands."""

    @bot.command()
    @lightbulb.add_checks(lightbulb.has_guild_permissions(hikari.Permissions.MANAGE_MESSAGES))
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("amount", "Number of messages to delete", type=int, min_value=1, max_value=100)
    @lightbulb.command("purge", "Deletes a specified amount of messages from a channel")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def purge(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        amount = ctx.options.amount
        channel_name = await bot.rest.fetch_channel(ctx.channel_id)
        if amount < 1:
            await ctx.respond("`The amount of messages to delete must be greater than 0.`")
            return
        if amount > 100:
            await ctx.respond("`You can only delete up to 100 messages at a time.`")
            return
        await ctx.respond(f"Deleting {ctx.options.amount} in #{channel_name}")
        async for message in bot.rest.fetch_messages(ctx.channel_id):
            if amount == 0:
                break
            await bot.rest.delete_message(ctx.channel_id, message.id)
            amount -= 1
            await asyncio.sleep(0.5)
        await bot.rest.create_message(ctx.channel_id, f"Deleted `{ctx.options.amount}` messages.")

    @bot.command
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("type", "Activity type", choices=["Playing", "Watching", "Listening"], required=False)
    @lightbulb.option("display", "What do you think?")
    @lightbulb.command("set", "Only for rawfish")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def set_status(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        display_status = ctx.options.display
        activity_type = hikari.ActivityType.WATCHING
        if ctx.options.type == "Playing":
            activity_type = hikari.ActivityType.PLAYING
        elif ctx.options.type == "Listening":
            activity_type = hikari.ActivityType.LISTENING

        config.DISPLAY_STATUS = display_status
        await ctx.respond(f"Changed activity to `{display_status}`")
        await bot.update_presence(
            activity=hikari.Activity(name=display_status, type=activity_type),
            status=hikari.Status.ONLINE,
        )

    @bot.command()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.command("scan", "scan local cached data")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def local_curves(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        option_labels = [label for label in config.local_curve_data.keys() if label != "user"]
        if not option_labels:
            await ctx.respond("No local curve data loaded.")
            return

        view = miru.View(timeout=180)
        select_options = [miru.SelectOption(label=option) for option in option_labels]
        text_select = LocalCurveSelect(placeholder="Select a user to load data", options=select_options)
        view.add_item(text_select)
        view.add_item(GraphButton())
        view.add_item(SplineButton())
        view.add_item(RegressionButton())

        message = await ctx.respond("Local data analyze complete", components=view)
        await view.start(message)
        await view.wait()

    @bot.command()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("folder", "path", choices=["user_img", "bot", "log", "data"], required=True)
    @lightbulb.command("open", "Open folder")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def show_files(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        folder_map = {
            "user_img": config.USER_IMG_PATH,
            "bot": config.BOT_PATH,
            "log": config.LOG_PATH,
            "data": config.DATA_PATH,
        }
        directory = folder_map.get(ctx.options.folder)
        if not directory or not Path(directory).exists():
            await ctx.respond("Target folder does not exist.")
            return

        files_in_folder = [entry.name for entry in Path(directory).iterdir() if entry.is_file()]
        display = f"Files in {directory}:\n"
        for file_name in files_in_folder:
            display += f"- {file_name}\n"
        await ctx.respond(display)

