"""Item-related commands."""

import os
import time
import hikari
import lightbulb
from lib.utils import check_user_access
from lib.config import BOT_PATH, RESOURCES_PATH, CHANGELOG_PATH, USER_IMG_PATH, DATA_PATH, item_map, stat_mapping
from lib.item_utils import ItemUtils
from lib.item_weight import WeightManager
from lib.price_estimator import PriceEstimator


def load_item_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load all item-related commands."""
    
    item_utils = bot.managers.get("item_utils", ItemUtils(item_map))
    weight_manager = bot.managers.get("weight_manager")
    price_estimator = bot.managers.get("price_estimator", PriceEstimator(output_path=USER_IMG_PATH / "pricecheck"))
    
    @bot.command()
    @lightbulb.command('item', 'Items for wynn')
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def items(ctx: lightbulb.Context):
        pass

    @items.child()
    @lightbulb.option('item', 'Name of the item')
    @lightbulb.command('search', 'Search with name')
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_find(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        item_name = ctx.options.item
        result = item_utils.item_search(item_name)
        if result:
            display, IDs, icon_id, lore, item_type = result
            display_name = item_utils._get_item_by_name(item_name)[0] or item_name
            
            item_embed = hikari.Embed(title=display_name, description="Data from Official Wynncraft ItemDatabase",
                                      color="#ACFFF2")
            item_embed.add_field("Base Stats", f"```json\n{display['base']}```")
            if display['id']:
                item_embed.add_field("Indentifications", f"```json\n{display['id']}```")
            if lore:
                item_embed.add_field("Lore", f"*{lore}*")
            try:
                if item_type in ["helmet", "chestplate", "leggings", "boots"]:
                    item_url = hikari.files.File(str(RESOURCES_PATH / f"{item_type}.png"))
                    item_embed.set_thumbnail(item_url)
                elif icon_id:
                    item_url = f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp"
                    item_embed.set_thumbnail(item_url)
            except Exception as error:
                print(f"Item thumbnail error: {error}")
                pass
            item_embed.set_footer("Nori Bot - Wynn Items")
            await ctx.respond(item_embed)
        else:
            item_embed = hikari.Embed(title="No Result Found")
            await ctx.respond(item_embed)

    @items.child()
    @lightbulb.option('amp', 'Amplifier tier (1-20)', required=False, default=0, min_value=0, max_value=20, type=int)
    @lightbulb.option('item', 'Name of the item')
    @lightbulb.command('roll', 'Item identifier simulator')
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_reroll_amp(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.config import item_amp_data
        user = await bot.rest.fetch_user(ctx.user.id)
        item_name = ctx.options.item
        tier = ctx.options.amp
        amp_tier = tier
        temp_data = {
            "item": item_name,
            "rr": 1,
            "tier": amp_tier
        }
        item_amp_data.update({user: temp_data})
        try:
            amp_result = item_utils.item_amp(item_name, amp_tier)
            rr_display = amp_result[1]
            try:
                icon_id = amp_result[3]
            except Exception as error:
                icon_id = None
                print(error)
            display = amp_result[0]
            item_type = amp_result[4]
            web_page = f"[Item Simulation on Nori-Web](https://nori.fish/wynn/item/simulation/)"
            item_embed = hikari.Embed(title="Item Identification Simulator",
                                      description=f'{web_page}\n*\"99% of gamblers quit before hitting it big\"*', color="#00E7B6")
            item_embed.add_field("Identifications:", f"```json\n{rr_display}```")
            if amp_tier > 0:
                item_embed.add_field(f"Amplifier {amp_tier}", display)
            try:
                if item_type in ["helmet", "chestplate", "leggings", "boots"]:
                    item_url = hikari.files.File(str(RESOURCES_PATH / f"{item_type}.png"))
                    item_embed.set_thumbnail(item_url)
                elif icon_id:
                    item_url = f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp"
                    item_embed.set_thumbnail(item_url)
            except Exception as error:
                print(f"Item thumbnail error: {error}")
                pass
            item_embed.set_footer("Nori Bot - Wynn Items")
            from lib.views.items import ampView
            view = ampView(timeout=60)
            message = await ctx.respond(embed=item_embed, components=view.build())
            message = await message
            await view.start(message)
            await view.wait()
        except Exception as error:
            print(f"Amp Item Data error: {error}")
            item_embed = hikari.Embed(title=f"Item {item_name} has no rerollable ID")
            await ctx.respond(embed=item_embed)

    @items.child()
    @lightbulb.command("changelog", "Item changelog based on API")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_check_log(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        log_file = hikari.files.File(str(CHANGELOG_PATH / "item_changelog.md"))
        await ctx.respond(log_file)

    @items.child()
    @lightbulb.option("stat_7", "7th stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_6", "6th stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_5", "5th stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_4", "4th stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_3", "3rd stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_2", "2nd stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_1", "1st stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("item", "Item name (Mythic only)", required=True)
    @lightbulb.command("evaluate", "Manual mythic weighing")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_evaluation(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.item_weight import mythic_weigh, weigh_scale
        from lib.config import DATA_PATH
        stat_1 = ctx.options.stat_1
        stat_2 = ctx.options.stat_2
        stat_3 = ctx.options.stat_3
        stat_4 = ctx.options.stat_4
        stat_5 = ctx.options.stat_5
        stat_6 = ctx.options.stat_6
        stat_7 = ctx.options.stat_7
        item_name = ctx.options.item
        stats = [stat_1, stat_2, stat_3, stat_4, stat_5, stat_6, stat_7]
        weight_data = mythic_weigh(item_name, stats, str(DATA_PATH / "mythic_weights.json"))
        if weight_data:
            result = weight_data[0]
            item = str(list(result.keys())[0])
            weight = weight_data[1]
            scale_display = ""
            scale_data = weigh_scale(item_name, str(DATA_PATH / "mythic_weights.json"))
            scale = scale_data[2]
            timestamp = scale_data[1]
            display_name = scale_data[3]
            item_data = item_utils.item_search(item_name)
            try:
                icon_id = item_data[2] if item_data else None
            except Exception as error:
                icon_id = None
                print(error)
            item_type = item_data[4] if item_data else None
            user_input = f"Input %: `{stat_1}, {stat_2}, {stat_3}, {stat_4}, {stat_5}, {stat_6}, {stat_7}`"
            overall = result[item]["Main"]
            response = f"**{display_name}** Weighted Overall: **{overall}**%"
            for val, stat in zip(weight, scale.items()):
                scale_display += f"[{val:.1f}/{float(stat[1]):.1f}] {str(stat[0])} {float(stat[1])}%\n"
            evaluate_embed = hikari.Embed(title=f"Mythic Item Evaluation", description=user_input, color="#9823F9")
            evaluate_embed.add_field(f"{display_name} (Main Scale)", f"```json\n{scale_display}```\n{response}")
            evaluate_embed.add_field("Latest data update", f"<t:{timestamp}>")
            try:
                if item_type in ["helmet", "chestplate", "leggings", "boots"]:
                    item_url = hikari.files.File(str(RESOURCES_PATH / f"{item_type}.png"))
                    evaluate_embed.set_thumbnail(item_url)
                elif icon_id:
                    item_url = f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp"
                    evaluate_embed.set_thumbnail(item_url)
            except Exception as error:
                print(error)
                pass
            evaluate_embed.set_footer("Nori Bot - Mythic evaluate")
            await ctx.respond(embed=evaluate_embed)
        else:
            await ctx.respond(f"No available scale for {item_name}")

    @items.child()
    @lightbulb.option("stat_7", "7th stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_6", "6th stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_5", "5th stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_4", "4th stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_3", "3rd stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_2", "2nd stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("stat_1", "1st stat on the scale", required=False, type=float, max_value=100, default=0)
    @lightbulb.option("item", "Item name (Mythic only)", required=True)
    @lightbulb.command("pc", "Manual Price-checker")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_pc(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        announcement_url = os.getenv('ANNOUNCEMENT_URL', 'https://discord.com/channels/...')
        recruitment_url = os.getenv('RECRUITMENT_URL', 'https://discord.com/channels/...')
        disabled_embed = hikari.Embed(
            title="Pricechecker Temporarily Disabled",
            description=f"For more information, read [Annoucement]({announcement_url}) in support server",
            color="#FFF000"
        )
        info = (
            "Pricechecking functions are temporarily disabled until the market crowdsources data and full integration is complete.\n\n"
            f"We are looking for volunteers to participate in a ML approach to price estimation\nRead [here]({recruitment_url}) if interested\n"
        )
        disabled_embed.add_field(name="Important Notice", value=info, inline=False)
        disabled_embed.set_footer(text="Nori Bot - Item Price Checker")
        await ctx.respond(embed=disabled_embed)

    @items.child()
    @lightbulb.command("pricecheck", "Auto price-checker with Encoded item (Mythic)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_pricecheck(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        import os
        announcement_url = os.getenv('ANNOUNCEMENT_URL', 'https://discord.com/channels/...')
        recruitment_url = os.getenv('RECRUITMENT_URL', 'https://discord.com/channels/...')
        disabled_embed = hikari.Embed(
            title="Pricechecker Temporarily Disabled",
            description=f"For more information, read [Annoucement]({announcement_url}) in support server",
            color="#FFF000"
        )
        info = (
            "Pricechecking functions are temporarily disabled until the market crowdsources data and full integration is complete.\n\n"
            f"We are looking for volunteers to participate in a ML approach to price estimation\nRead [here]({recruitment_url}) if interested\n"
        )
        disabled_embed.add_field(name="Important Notice", value=info, inline=False)
        disabled_embed.set_footer(text="Nori Bot - Item Price Checker")
        await ctx.respond(embed=disabled_embed)

    @items.child()
    @lightbulb.option("item", "In game item from Wynntils F3")
    @lightbulb.command("weigh", "Auto Weighing with Encoded Item (Mythic)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_auto_weigh(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.decoders import ItemDecoder
        from lib.config import item_map
        from lib.item_weight import item_weight_output, weigh_scale
        user = await bot.rest.fetch_user(ctx.user.id)
        initial_embed = hikari.Embed(title=f"Mythic weighing requested by {user}", description="Processing...",
                                    color="#9823F9")
        await ctx.respond(embed=initial_embed)
        item_string = ctx.options.item
        decoder = ItemDecoder()
        result = decoder.decode_item_string(item_string, item_map)
        if result:
            item_output = item_weight_output(item_string, item_map)
            if item_output:
                item_name = str(list(item_output.keys())[0])
                scales = item_output[item_name]
                max_scale = max(scales, key=scales.get)
                overall = scales[max_scale]
                scale_data = weigh_scale(item_name)
                scale = scale_data[2]
                timestamp = scale_data[1]
                display_name = scale_data[3]
                item_data = item_utils.item_search(item_name)
                try:
                    icon_id = item_data[2] if item_data else None
                except Exception as error:
                    icon_id = None
                    print(error)
                item_type = item_data[4] if item_data else None
                display = ""
                stats = result.stats
                rates = result.rates
                for stat_id, value in stats.items():
                    rate = rates.get(stat_id, 0)
                    stat_name = stat_mapping.get(stat_id, stat_id)
                    display += f"{value} {stat_name} [{rate}%]\n"
                user_input = f"Weight % Based on {max_scale} Scale."
                response = f"**{display_name}** Weighted Overall: **{overall}**%"
                scale_display = ""
                for stat in scale.items():
                    scale_display += f"{str(stat[0])} {float(stat[1])}%\n"
                weigh_embed = hikari.Embed(title=f"Mythic Item Weighing", description=user_input, color="#9823F9")
                if result.shiny:
                    display = f"*{result.shiny}*\n" + display
                weigh_embed.add_field(f"{display_name} (Main Scale)", f"```json\n{scale_display}```\n{response}")
                weigh_embed.add_field("Item Stats", f"```json\n{display}```")
                weigh_embed.add_field("Latest data update", f"<t:{timestamp}>")
                try:
                    if item_type in ["helmet", "chestplate", "leggings", "boots"]:
                        item_url = hikari.files.File(str(RESOURCES_PATH / f"{item_type}.png"))
                        weigh_embed.set_thumbnail(item_url)
                    elif icon_id:
                        item_url = f"https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp"
                        weigh_embed.set_thumbnail(item_url)
                except Exception as error:
                    print(error)
                    pass
                weigh_embed.set_footer("Nori Bot - Mythic weighing")
                await ctx.edit_last_response(embed=weigh_embed)
            else:
                error_embed = hikari.Embed(title=f"No available scale for {item_string}",
                                           description="Currently only support mythic-tier items",
                                           color="#9823F9")
                await ctx.edit_last_response(embed=error_embed)
        else:
            error_embed = hikari.Embed(title=f"Error while decoding {item_string}",
                                       description="Contact support server for any issue.",
                                       color="#9823F9")
            await ctx.edit_last_response(embed=error_embed)

    @items.child()
    @lightbulb.option("item", "Item name (Mythic only)", required=True)
    @lightbulb.command("scale", "Weighing scale for mythic")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_scale(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.item_weight import weigh_scale
        from lib.config import DATA_PATH
        item_name = ctx.options.item
        scale_data = weigh_scale(item_name, str(DATA_PATH / "mythic_weights.json"))
        if scale_data:
            scale = scale_data[2]
            timestamp = scale_data[1]
            display_name = scale_data[3]
            scale_display = ""
            for stat in scale.items():
                scale_display += f"{str(stat[0])} {float(stat[1])}%\n"
            scale_embed = hikari.Embed(title=f"Mythic Item Scale", description=f"**{display_name}**", color="#9823F9")
            scale_embed.add_field("Weighing Scale (Main)", f"```json\n{scale_display}```")
            scale_embed.add_field("Latest data update", f"<t:{timestamp}>")
            scale_embed.set_footer("Nori Bot - Mythic scale")
            await ctx.respond(embed=scale_embed)
        else:
            await ctx.respond(f"No available scale for {item_name}")

    @items.child()
    @lightbulb.option("item", "In game item from Wynntils F3")
    @lightbulb.command("check", "Decode an item and display its IDs (All Items)")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_check(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.decoders import ItemDecoder
        from lib.config import item_map, stat_mapping
        item_string = ctx.options.item
        decoder = ItemDecoder()
        result = decoder.decode_item_string(item_string, item_map)
        if result:
            display = ""
            stats = result.stats
            rates = result.rates
            for stat_id, value in stats.items():
                rate = rates.get(stat_id, 0)
                stat_name = stat_mapping.get(stat_id, stat_id)
                display += f"{value} {stat_name} [{rate}%]\n"
            check_embed = hikari.Embed(title="Item Decode", description="Item stats from Wynntils", color="#ACFFF2")
            if result.shiny:
                display = f"*{result.shiny}*\n" + display
            check_embed.add_field("Identifications", f"```json\n{display}```")
            check_embed.set_footer("Nori Bot - Item Decode")
            await ctx.respond(embed=check_embed)
        else:
            error_embed = hikari.Embed(title=f"Error while decoding {item_string}",
                                       description="Contact support server for any issue.",
                                       color="#ACFFF2")
            await ctx.respond(embed=error_embed)

    @items.child()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("price", "Price in stacks", type=float, required=True)
    @lightbulb.option("item", "Item name (Mythic only)", required=True)
    @lightbulb.command("sales", "Submit item sales")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_sales(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        import os
        import json
        from lib.config import sales_data, DATA_PATH
        item_name = ctx.options.item
        price = ctx.options.price
        user = await bot.rest.fetch_user(ctx.user.id)
        username = user.username
        
        if item_name not in sales_data:
            sales_data[item_name] = []
        
        sales_data[item_name].append({
            "price": price,
            "seller": username,
            "timestamp": int(time.time())
        })
        
        try:
            with open(DATA_PATH / "sales_data.json", "w") as file:
                json.dump(sales_data, file, indent=2)
            sales_embed = hikari.Embed(title="Sale Submitted", description=f"Thank you {username}!", color="#51FFCA")
            sales_embed.add_field(item_name, f"Price: {price} stacks")
            sales_embed.set_footer("Nori Bot - Sales Submission")
            await ctx.respond(embed=sales_embed)
        except Exception as error:
            print(f"Error saving sales data: {error}")
            await ctx.respond("Error saving sale data. Please contact support.")

    @items.child()
    @lightbulb.command("lootpool", "Weekly Lootpool Rotation")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_lootpool(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.views.items import lootView
        view = lootView(timeout=120)
        message = await ctx.respond(f"Select a week", components=view.build())
        message = await message
        await view.start(message)
        await view.wait()

    @items.child()
    @lightbulb.option("item", "Item name", required=True)
    @lightbulb.command("history", "Find item in the lootpool history")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def item_history(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        from lib.utils import get_loot_history
        item_name = ctx.options.item
        history = get_loot_history(item_name)
        if history:
            history_embed = hikari.Embed(title=f"Lootpool History for {item_name}", color="#ACFFF2")
            history_embed.add_field("History", f"```json\n{history}```")
            history_embed.set_footer("Nori Bot - Lootpool History")
            await ctx.respond(embed=history_embed)
        else:
            await ctx.respond(f"No history found for {item_name}")

