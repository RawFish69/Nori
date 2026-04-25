"""Server-related owner commands."""

import asyncio
import json

import hikari
import lightbulb

from lib.config import BOT_PATH
from lib.utils import check_user_access


def load_server_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load server commands."""

    @bot.command
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.command("server", "server related commands")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def server(ctx: lightbulb.Context):
        pass

    @server.child()
    @lightbulb.command("count", "Quick count")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def server_count(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Processing joined servers...")
        servers = await bot.rest.fetch_my_guilds()
        server_count = len(servers)
        await ctx.edit_last_response(f"Total of `{server_count}` servers.")

    @server.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.command("list", "Joined list")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def server_list(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        await ctx.respond("Fetching server list")

        servers = await bot.rest.fetch_my_guilds()
        total_servers = len(servers)
        server_count = 0
        user_count = 0
        blocker = 0
        server_group_data = {}
        channel_id = ctx.channel_id

        await ctx.edit_last_response(f"## Start server list scan ##\n### Estimated {total_servers} servers ###")

        for server_obj in servers:
            try:
                guild_preview = await bot.rest.fetch_guild_preview(server_obj.id)
                server_users = guild_preview.approximate_member_count
                guild = await bot.rest.fetch_guild(server_obj.id)
                server_owner = await bot.rest.fetch_user(guild.owner_id)

                user_count += server_users
                server_count += 1
                blocker += 1

                server_info = {"owner": str(server_owner), "users": int(server_users), "id": server_obj.id}
                server_group_data[server_obj.name] = server_info

                if blocker == 5:
                    progress = f"**[{round((server_count / total_servers) * 100, 2)}%]** {server_count} servers - `{user_count}` users in total."
                    await bot.rest.create_message(channel=channel_id, content=progress)
                    blocker = 0
                    await asyncio.sleep(1)

                if server_count % 100 == 0:
                    sorted_data = {
                        key: value
                        for key, value in sorted(server_group_data.items(), key=lambda item: item[1]["users"], reverse=True)
                    }
                    with open(BOT_PATH / "server_data.json", "w", encoding="utf-8") as file:
                        json.dump(sorted_data, file, indent=3)

                await asyncio.sleep(1)
            except hikari.errors.UnauthorizedError as error:
                print(f"UnauthorizedError: {error}")
                await ctx.edit_last_response("There was an error with the webhook token.")
                continue
            except hikari.errors.NotFoundError as error:
                print(f"NotFoundError: {error}")
                await asyncio.sleep(5)
                continue
            except Exception as error:
                print(f"An error occurred: {error}")
                await ctx.edit_last_response("An unexpected error occurred.")
                continue

        sorted_data = {
            key: value for key, value in sorted(server_group_data.items(), key=lambda item: item[1]["users"], reverse=True)
        }
        with open(BOT_PATH / "server_data.json", "w", encoding="utf-8") as file:
            json.dump(sorted_data, file, indent=3)

        user = await bot.rest.fetch_user(ctx.user.id)
        finish = f"{user.mention} Scan Complete: {user_count} users in {server_count} servers."
        await bot.rest.create_message(channel=channel_id, content=finish, user_mentions=True)

