"""Server-related owner commands."""
import asyncio
import json
import hikari
import lightbulb
from lib.config import BOT_PATH
loader = lightbulb.Loader()
server = lightbulb.Group('server', 'server related commands')

@server.register
class ServerCount(lightbulb.SlashCommand, name='count', description='Quick count', hooks=[lightbulb.prefab.owner_only]):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond('Processing joined servers...')
        servers = await ctx.client.app.rest.fetch_my_guilds()
        server_count = len(servers)
        await ctx.edit_response(-1, f'Total of `{server_count}` servers.')

@server.register
class ServerList(lightbulb.SlashCommand, name='list', description='Joined list', hooks=[lightbulb.prefab.owner_only, lightbulb.prefab.owner_only]):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond('Fetching server list')
        servers = await ctx.client.app.rest.fetch_my_guilds()
        total_servers = len(servers)
        server_count = 0
        user_count = 0
        blocker = 0
        server_group_data = {}
        channel_id = ctx.channel_id
        await ctx.edit_response(-1, f'## Start server list scan ##\n### Estimated {total_servers} servers ###')
        for server_obj in servers:
            try:
                guild_preview = await ctx.client.app.rest.fetch_guild_preview(server_obj.id)
                server_users = guild_preview.approximate_member_count
                guild = await ctx.client.app.rest.fetch_guild(server_obj.id)
                server_owner = await ctx.client.app.rest.fetch_user(guild.owner_id)
                user_count += server_users
                server_count += 1
                blocker += 1
                server_info = {'owner': str(server_owner), 'users': int(server_users), 'id': server_obj.id}
                server_group_data[server_obj.name] = server_info
                if blocker == 5:
                    progress = f'**[{round(server_count / total_servers * 100, 2)}%]** {server_count} servers - `{user_count}` users in total.'
                    await ctx.client.app.rest.create_message(channel=channel_id, content=progress)
                    blocker = 0
                    await asyncio.sleep(1)
                if server_count % 100 == 0:
                    sorted_data = {key: value for key, value in sorted(server_group_data.items(), key=lambda item: item[1]['users'], reverse=True)}
                    with open(BOT_PATH / 'server_data.json', 'w', encoding='utf-8') as file:
                        json.dump(sorted_data, file, indent=3)
                await asyncio.sleep(1)
            except hikari.errors.UnauthorizedError as error:
                print(f'UnauthorizedError: {error}')
                await ctx.edit_response(-1, 'There was an error with the webhook token.')
                continue
            except hikari.errors.NotFoundError as error:
                print(f'NotFoundError: {error}')
                await asyncio.sleep(5)
                continue
            except Exception as error:
                print(f'An error occurred: {error}')
                await ctx.edit_response(-1, 'An unexpected error occurred.')
                continue
        sorted_data = {key: value for key, value in sorted(server_group_data.items(), key=lambda item: item[1]['users'], reverse=True)}
        with open(BOT_PATH / 'server_data.json', 'w', encoding='utf-8') as file:
            json.dump(sorted_data, file, indent=3)
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        finish = f'{user.mention} Scan Complete: {user_count} users in {server_count} servers.'
        await ctx.client.app.rest.create_message(channel=channel_id, content=finish, user_mentions=True)
loader.command(server)
