"""Runtime event hooks shared by the modular bot."""

import logging

import hikari
import lightbulb

import lib.config as config


def _format_raw_options(raw_options) -> str:
    if not raw_options:
        return ""
    try:
        return " ".join(f"{option.name}={option.value}" for option in raw_options)
    except Exception:
        return str(raw_options)


def load_event_hooks(bot: lightbulb.BotApp):
    """Register startup presence and command log hooks."""

    @bot.listen(hikari.StartedEvent)
    async def _set_startup_presence(event: hikari.StartedEvent):
        await bot.update_presence(
            activity=hikari.Activity(name=config.DISPLAY_STATUS, type=hikari.ActivityType.WATCHING),
            status=hikari.Status.ONLINE,
        )

    @bot.listen()
    async def _command_log(event: lightbulb.CommandCompletionEvent):
        if not config.COMMAND_LOG_CHANNEL_ID:
            return

        context = event.context
        command_name = event.command.qualname
        option_display = _format_raw_options(getattr(context, "raw_options", None))
        command_display = f"/{command_name}" + (f" {option_display}" if option_display else "")

        try:
            channel = await bot.rest.fetch_channel(context.channel_id)
            server = await bot.rest.fetch_guild(context.guild_id) if context.guild_id else None
        except Exception:
            channel = None
            server = None

        if server and channel:
            message = f"{server} #{channel} **{context.author}**: `{command_display}`"
            logging.info("%s #%s %s: %s", server, channel, context.author, command_display)
        else:
            message = f"<DM> **{context.author}**: `{command_display}`"
            logging.info("<DM> %s: %s", context.author, command_display)

        try:
            await bot.rest.create_message(channel=config.COMMAND_LOG_CHANNEL_ID, content=message)
        except Exception as error:
            print(f"Unable to write command log message: {error}")
