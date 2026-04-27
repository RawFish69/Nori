"""Runtime event hooks shared by the modular bot.

Command audit events are recorded for data collection and statistics purposes.
"""

import logging

import hikari
import lightbulb

import lib.config as config

_GUILD_NAME_CACHE: dict[int, str] = {}


def _format_raw_options(raw_options) -> str:
    if not raw_options:
        return ""
    try:
        return " ".join(f"{option.name}={option.value}" for option in raw_options)
    except Exception:
        return str(raw_options)


def _collect_option_path_and_values(options) -> tuple[list[str], list[str]]:
    path = []
    values = []
    for option in options or []:
        name = getattr(option, "name", None)
        nested = getattr(option, "options", None)
        value = getattr(option, "value", None)
        if nested:
            if name:
                path.append(str(name))
            child_path, child_values = _collect_option_path_and_values(nested)
            path.extend(child_path)
            values.extend(child_values)
        elif name:
            if value is None:
                path.append(str(name))
            else:
                values.append(f"{name}={value}")
    return path, values


def _format_interaction_command(interaction) -> str | None:
    command_name = getattr(interaction, "command_name", None)
    if not command_name:
        return None
    path, values = _collect_option_path_and_values(getattr(interaction, "options", None))
    command_display = "/" + " ".join([str(command_name), *path])
    return command_display + (f" {' '.join(values)}" if values else "")


def _cache_get(cache, method_name: str, snowflake):
    try:
        method = getattr(cache, method_name, None)
        return method(snowflake) if method and snowflake else None
    except Exception:
        return None


def _snowflake_key(snowflake) -> int | None:
    try:
        return int(snowflake)
    except (TypeError, ValueError):
        return None


async def _guild_name(bot: lightbulb.BotApp, guild_id) -> str:
    guild_key = _snowflake_key(guild_id)
    if guild_key is not None and guild_key in _GUILD_NAME_CACHE:
        return _GUILD_NAME_CACHE[guild_key]

    guild = _cache_get(getattr(bot, "cache", None), "get_guild", guild_id)
    guild_name = getattr(guild, "name", None)
    if not guild_name:
        try:
            guild_name = getattr(await bot.rest.fetch_guild(guild_id), "name", None)
        except Exception:
            guild_name = None
    guild_name = guild_name or str(guild_id)
    if guild_key is not None:
        _GUILD_NAME_CACHE[guild_key] = guild_name
    return guild_name


def load_event_hooks(bot: lightbulb.BotApp):
    """Register startup presence and local command audit hooks."""

    @bot.listen(hikari.StartedEvent)
    async def _set_startup_presence(event: hikari.StartedEvent):
        await bot.update_presence(
            activity=hikari.Activity(name=config.DISPLAY_STATUS, type=hikari.ActivityType.WATCHING),
            status=hikari.Status.ONLINE,
        )

    @bot.listen()
    async def _command_log(event: hikari.InteractionCreateEvent):
        interaction = event.interaction
        interaction_type = getattr(interaction, "type", None)
        application_command_type = getattr(hikari.InteractionType, "APPLICATION_COMMAND", None)
        if application_command_type is not None and interaction_type != application_command_type:
            return
        command_display = _format_interaction_command(interaction)
        if not command_display:
            return

        author = getattr(interaction, "user", None)
        if author is None and getattr(interaction, "member", None):
            author = getattr(interaction.member, "user", None)
        author = author or "Unknown user"
        guild_id = getattr(interaction, "guild_id", None)

        if guild_id:
            guild_name = await _guild_name(bot, guild_id)
            logging.info(
                "Guild %s %s: %s",
                guild_name,
                author,
                command_display,
            )
        else:
            logging.info("<DM> %s: %s", author, command_display)
