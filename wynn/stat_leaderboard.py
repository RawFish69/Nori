import hikari
import miru

# Previous code from nori-bot main

class statView(miru.View):

    # Button Sample

    async def button_playtime(self, button: miru.Button, ctx: miru.Context):
        user = await bot.rest.fetch_user(ctx.user.id)
        default_embed = hikari.Embed(title=f"Processing Playtime Leaderboard\nPlease be patient",
                                     color="#AEB1B1")
        await ctx.edit_response(embed=default_embed)
        lb_user_cache[ctx.user.username]["type"] = "Playtime"
        await self.lb_display(ctx, lb_user_cache[ctx.user.username]["page"], lb_user_cache[ctx.user.username]["type"])

    # Display handling sample

    async def lb_display(self, ctx: miru.Context, page_num, stat_type):
        ranking_data = await stat_leaderboard(stat_type)
        top_players = ranking_data[(page_num-1)*10: page_num*10]

        stat_map = {
            "Chest": "Opened",
            "Dungeon": "Clears",
            "Playtime": "Hours ",
            # ... Add as needed
        }
        max_name_length = max([len(list(name.keys())[0]) for name in top_players] + [6])  # 6 is for 'Player'
        max_clears_length = max([len(str(list(clears.values())[0])) for clears in top_players] + [6])  # 6 is for 'Clears'

        border_line = '╠═════╬' + '═' * (max_name_length + 2) + '╬' + '═' * (max_clears_length + 2) + '╣\n'
        header = '```json\n'
        header += '╔═════╦' + '═' * (max_name_length + 2) + '╦' + '═' * (max_clears_length + 2) + '╗\n'
        header += f'║  #  ║ {"Player":<{max_name_length}} ║ {stat_map[stat_type]} ║\n'
        header += border_line

        display = header
        for index, player in enumerate(top_players):
            name = list(player.keys())[0]
            clears = list(player.values())[0]
            display += f'║ {(page_num - 1) * 10 + (index + 1):3d} ║ {name:<{max_name_length}} ║ {clears:>{max_clears_length}} ║\n'
        display += '╚═════╩' + '═' * (max_name_length + 2) + '╩' + '═' * (max_clears_length + 2) + '╝```'
        stat_embed = hikari.Embed(title="Wynncraft Stats Leaderboard", color="#D78CFF")
        stat_embed.add_field(f"{stat_type} Leaderboard", f"{display}")
        stat_embed.set_footer("Nori Bot - Wynn Stats Leaderboard")
        await ctx.edit_response(embed=stat_embed)

    @miru.button(label='menu', style=hikari.ButtonStyle.SUCCESS, row=2)
    async def button_menu(self, button: miru.Button, ctx: miru.Context):
        user = await bot.rest.fetch_user(ctx.user.id)
        msg = '```json\n'
        title_line = 'Wynncraft Leaderboard\n'
        description_line = f"Select a leaderboard category"
        msg += '1. Chest Opened\n'
        msg += '2. Mobs Killed\n'
        msg += '3. Wars Completed\n'
        msg += '4. Dungeon Clears\n'
        msg += '5. XP Contribution```\n'
        stat_embed = hikari.Embed(title=title_line, description=description_line, color="#93FEFD")
        stat_embed.add_field("Information:", f"{msg}")
        stat_embed.set_thumbnail("https://cdn.wynncraft.com/nextgen/wynncraft_icon.png")
        stat_embed.set_footer("Nori Bot - Wynn Stats Leaderboard")
        await ctx.edit_response(stat_embed)


    # Sample navigation handling
    @miru.button(emoji="▶", style=hikari.ButtonStyle.SECONDARY, row=2)
    async def button_next_page(self, button: miru.Button, ctx: miru.Context):
        if lb_user_cache[ctx.user.username]["type"] and lb_user_cache[ctx.user.username]["page"] < 10:
            lb_user_cache[ctx.user.username]["page"] += 1
            await self.lb_display(ctx, lb_user_cache[ctx.user.username]["page"], lb_user_cache[ctx.user.username]["type"])
        elif lb_user_cache[ctx.user.username]["page"] == 10: # Currently 10x10 max
            await ctx.respond("This is the last page.", flags=hikari.MessageFlag.EPHEMERAL)
        else:
            await ctx.respond("Pick a raid type or Do `/lb raid` first", flags=hikari.MessageFlag.EPHEMERAL)


    # Action upon timeout
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as e:
            print(f"Failed to edit message on timeout: {e}")