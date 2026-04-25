"""Social and status commands."""

import time
from datetime import datetime

import hikari
import lightbulb

import lib.config as config
from lib.utils import check_user_access


def _uptime_display(start_time: float):
    up_time = int(time.time() - start_time)
    minutes, seconds = divmod(up_time, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    return f"**{days:2d}** d **{hours:2d}** h **{minutes:2d}** m **{seconds:2d}** s"


def load_social_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load social/status commands."""

    @bot.command
    @lightbulb.command("status", "Check bot status")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def check_status(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        time_display = _uptime_display(config.deploy_time)
        display = "`Nori - Discord Chatbot by RawFish`\n"
        display += f"Current Mode: __**{config.mode}**__, Uptime: {time_display}.\n"
        display += f"Deployment: <t:{int(config.deploy_time)}:R>"
        await ctx.respond(display)

    @bot.command
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("type", "Select a mode", choices=config.MODE_LIST)
    @lightbulb.command("mode", "Change operation mode (Owner only)")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def change_mode(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        mode_choice = ctx.options.type
        config.mode = mode_choice
        if mode_choice == config.MODE_LIST[3]:
            status = hikari.Status.ONLINE
        else:
            status = hikari.Status.DO_NOT_DISTURB
        await bot.update_presence(
            activity=hikari.Activity(name=f"{config.mode} mode", type=hikari.ActivityType.PLAYING),
            status=status,
        )
        await ctx.respond(f"Operation mode changed to `{config.mode}`")

    @bot.command
    @lightbulb.command("hi", "say hello back")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def print_hello(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        user = await bot.rest.fetch_user(ctx.user.id)
        await ctx.respond(f"Shut up, {user}")

    @bot.command
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("content", "Text content")
    @lightbulb.option("channel", "Channel ID")
    @lightbulb.command("say", "Now we talking")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def bot_say(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        channel_id = ctx.options.channel
        text = ctx.options.content
        try:
            channel_name = await bot.rest.fetch_channel(channel_id)
            await bot.rest.create_message(channel=channel_id, content=text, user_mentions=True, role_mentions=True)
            await ctx.respond(f"Message `{text}` sent to channel `{channel_name}`")
        except Exception as error:
            await ctx.respond(f"Message cannot be sent, {error}.")

    @bot.command()
    @lightbulb.option("user_id", "User ID", type=hikari.User)
    @lightbulb.command("profile", "Get user profile")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def get_profile(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        try:
            username = ctx.options.user_id
            if not isinstance(username, hikari.User):
                username = await bot.rest.fetch_user(ctx.options.user_id)
            user_pfp = username.avatar_url
            username_display = username.username
            user_created = datetime.strptime(str(username.created_at).split(".")[0], "%Y-%m-%d %H:%M:%S")
            user_flags = [flag for flag in username.flags]

            profile_embed = hikari.Embed(title=username_display, color="#EAEAEA")
            if user_pfp:
                profile_embed.set_image(user_pfp)
            profile_embed.add_field("Account created at", str(user_created))
            profile_embed.add_field("Badges", "".join(f"{str(flag)}\n" for flag in user_flags) if user_flags else "N/A")

            try:
                roles = ""
                guild = await bot.rest.fetch_guild(ctx.guild_id)
                guild_icon = guild.icon_url
                user_in_server = await bot.rest.fetch_member(guild, username)
                user_joined = datetime.strptime(str(user_in_server.joined_at).split(".")[0], "%Y-%m-%d %H:%M:%S")
                user_roles = user_in_server.get_roles()
                for role in user_roles:
                    if "everyone" not in role.name:
                        roles += role.name + "\n"
                if roles:
                    profile_embed.add_field("Server Member since", str(user_joined))
                    profile_embed.add_field(f"Roles in {guild.name}", roles)
                    if guild_icon:
                        profile_embed.set_thumbnail(guild_icon)
            except Exception as error:
                print(error)

            await ctx.respond(embed=profile_embed)
        except Exception as error:
            print(error)
            await ctx.respond("Invalid user ID")

