"""Item-related commands."""
import json
import os
import time
import hikari
import lightbulb
import lib.config as config
from lib.config import RESOURCES_PATH, CHANGELOG_PATH, DATA_PATH
from lib.item_utils import ItemUtils
from lib.permissions import sales_contributor_only
loader = lightbulb.Loader()

def _item_utils() -> ItemUtils:
    """Build ItemUtils from the live item map loaded during startup/refresh."""
    return ItemUtils(config.item_map or {})

def _load_lootpool_history() -> dict:
    if config.lootpool_history:
        return config.lootpool_history
    try:
        with open(DATA_PATH / 'lootpool_history.json', 'r', encoding='utf-8') as file:
            config.lootpool_history = json.load(file)
    except Exception as error:
        print(f'Error loading lootpool_history.json: {error}')
        config.lootpool_history = {}
    return config.lootpool_history

def _find_item_in_lootpool_history(item_name: str) -> dict:
    item_query = item_name.casefold()
    item_data = {}
    for week, weekly_pool in _load_lootpool_history().items():
        weekly_count = 0
        weekly_regions = []
        shiny_present = False
        shiny_region = None
        tracker = None
        if not isinstance(weekly_pool, dict):
            continue
        for region, pool_items in weekly_pool.items():
            if not isinstance(pool_items, list) or len(pool_items) < 2:
                continue
            shiny = str(pool_items[0])
            mythics = pool_items[1] if isinstance(pool_items[1], list) else []
            mythic_names = [str(item).casefold() for item in mythics]
            shiny_match = item_query in shiny.casefold()
            mythic_match = any((item_query in mythic for mythic in mythic_names))
            if shiny_match or mythic_match:
                weekly_count += 1
                weekly_regions.append(str(region))
            if shiny_match:
                shiny_present = True
                shiny_region = str(region)
                tracker = shiny
        item_data[week] = {'count': weekly_count, 'shiny': shiny_present, 'region': weekly_regions, 'shiny_region': shiny_region, 'tracker': tracker}
    return item_data
items = lightbulb.Group('item', 'Items for wynn')

@items.register
class ItemFind(lightbulb.SlashCommand, name='search', description='Search with name'):
    item = lightbulb.string('item', 'Name of the item')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        item_utils = _item_utils()
        item_name = self.item
        result = item_utils.item_search(item_name)
        if result:
            display, IDs, icon_id, lore, item_type = result
            display_name = item_utils._get_item_by_name(item_name)[0] or item_name
            item_embed = hikari.Embed(title=display_name, description='Data from Official Wynncraft ItemDatabase', color='#ACFFF2')
            item_embed.add_field('Base Stats', f"```json\n{display['base']}```")
            if display['id']:
                item_embed.add_field('Indentifications', f"```json\n{display['id']}```")
            if lore:
                item_embed.add_field('Lore', f'*{lore}*')
            try:
                if item_type in ['helmet', 'chestplate', 'leggings', 'boots']:
                    item_url = hikari.files.File(str(RESOURCES_PATH / f'{item_type}.png'))
                    item_embed.set_thumbnail(item_url)
                elif icon_id:
                    item_url = f'https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp'
                    item_embed.set_thumbnail(item_url)
            except Exception as error:
                print(f'Item thumbnail error: {error}')
                pass
            item_embed.set_footer('Nori Bot - Wynn Items')
            await ctx.respond(item_embed)
        else:
            item_embed = hikari.Embed(title='No Result Found')
            await ctx.respond(item_embed)

@items.register
class ItemRerollAmp(lightbulb.SlashCommand, name='roll', description='Item identifier simulator'):
    item = lightbulb.string('item', 'Name of the item')
    amp = lightbulb.integer('amp', 'Amplifier tier (1-20)', default=0, min_value=0, max_value=20)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        item_utils = _item_utils()
        from lib.config import item_amp_data
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        item_name = self.item
        tier = self.amp
        amp_tier = tier
        temp_data = {'item': item_name, 'rr': 1, 'tier': amp_tier}
        item_amp_data.update({user: temp_data})
        try:
            amp_result = item_utils.item_amp(item_name, amp_tier)
            if not amp_result:
                item_embed = hikari.Embed(title=f'Item {item_name} has no rerollable ID')
                await ctx.respond(embed=item_embed)
                return
            rr_display = amp_result[1]
            try:
                icon_id = amp_result[3]
            except Exception as error:
                icon_id = None
                print(error)
            display = amp_result[0]
            item_type = amp_result[4]
            web_page = f'[Item Simulation on Nori-Web](https://nori.fish/wynn/item/simulation/)'
            item_embed = hikari.Embed(title='Item Identification Simulator', description=f'{web_page}\n*"99% of gamblers quit before hitting it big"*', color='#00E7B6')
            item_embed.add_field('Identifications:', f'```json\n{rr_display}```')
            if amp_tier > 0:
                item_embed.add_field(f'Amplifier {amp_tier}', display)
            try:
                if item_type in ['helmet', 'chestplate', 'leggings', 'boots']:
                    item_url = hikari.files.File(str(RESOURCES_PATH / f'{item_type}.png'))
                    item_embed.set_thumbnail(item_url)
                elif icon_id:
                    item_url = f'https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp'
                    item_embed.set_thumbnail(item_url)
            except Exception as error:
                print(f'Item thumbnail error: {error}')
                pass
            item_embed.set_footer('Nori Bot - Wynn Items')
            from lib.views.items import ampView
            view = ampView(timeout=60)
            message = await ctx.respond(embed=item_embed, components=view.build())
            message = await ctx.fetch_response(message)
            ctx.client.app.d.miru.start_view(view, bind_to=message)
            await view.wait()
        except Exception as error:
            print(f'Amp Item Data error: {error}')
            item_embed = hikari.Embed(title=f'Item {item_name} has no rerollable ID')
            await ctx.respond(embed=item_embed)

@items.register
class ItemCheckLog(lightbulb.SlashCommand, name='changelog', description='Item changelog based on API'):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        log_file = hikari.files.File(str(CHANGELOG_PATH / 'item_changelog.md'))
        await ctx.respond(log_file)

@items.register
class ItemEvaluation(lightbulb.SlashCommand, name='evaluate', description='Manual mythic weighing'):
    item = lightbulb.string('item', 'Item name (Mythic only)')
    stat_1 = lightbulb.number('stat_1', '1st stat on the scale', max_value=100, default=0)
    stat_2 = lightbulb.number('stat_2', '2nd stat on the scale', max_value=100, default=0)
    stat_3 = lightbulb.number('stat_3', '3rd stat on the scale', max_value=100, default=0)
    stat_4 = lightbulb.number('stat_4', '4th stat on the scale', max_value=100, default=0)
    stat_5 = lightbulb.number('stat_5', '5th stat on the scale', max_value=100, default=0)
    stat_6 = lightbulb.number('stat_6', '6th stat on the scale', max_value=100, default=0)
    stat_7 = lightbulb.number('stat_7', '7th stat on the scale', max_value=100, default=0)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        from lib.item_weight import mythic_weigh, weigh_scale
        from lib.config import DATA_PATH
        item_utils = _item_utils()
        stat_1 = self.stat_1
        stat_2 = self.stat_2
        stat_3 = self.stat_3
        stat_4 = self.stat_4
        stat_5 = self.stat_5
        stat_6 = self.stat_6
        stat_7 = self.stat_7
        item_name = self.item
        stats = [stat_1, stat_2, stat_3, stat_4, stat_5, stat_6, stat_7]
        weight_data = mythic_weigh(item_name, stats, str(DATA_PATH / 'mythic_weights.json'))
        if weight_data:
            result = weight_data[0]
            item = str(list(result.keys())[0])
            weight = weight_data[1]
            scale_display = ''
            scale_data = weigh_scale(item_name, str(DATA_PATH / 'mythic_weights.json'))
            if not scale_data:
                await ctx.respond(f'No available scale for {item_name}')
                return
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
            user_input = f'Input %: `{stat_1}, {stat_2}, {stat_3}, {stat_4}, {stat_5}, {stat_6}, {stat_7}`'
            overall = result[item]['Main']
            response = f'**{display_name}** Weighted Overall: **{overall}**%'
            for val, stat in zip(weight, scale.items()):
                scale_display += f'[{val:.1f}/{float(stat[1]):.1f}] {str(stat[0])} {float(stat[1])}%\n'
            evaluate_embed = hikari.Embed(title=f'Mythic Item Evaluation', description=user_input, color='#9823F9')
            evaluate_embed.add_field(f'{display_name} (Main Scale)', f'```json\n{scale_display}```\n{response}')
            evaluate_embed.add_field('Latest data update', f'<t:{timestamp}>')
            try:
                if item_type in ['helmet', 'chestplate', 'leggings', 'boots']:
                    item_url = hikari.files.File(str(RESOURCES_PATH / f'{item_type}.png'))
                    evaluate_embed.set_thumbnail(item_url)
                elif icon_id:
                    item_url = f'https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp'
                    evaluate_embed.set_thumbnail(item_url)
            except Exception as error:
                print(error)
                pass
            evaluate_embed.set_footer('Nori Bot - Mythic evaluate')
            await ctx.respond(embed=evaluate_embed)
        else:
            await ctx.respond(f'No available scale for {item_name}')

@items.register
class ItemPc(lightbulb.SlashCommand, name='pc', description='Manual Price-checker'):
    item = lightbulb.string('item', 'Item name (Mythic only)')
    stat_1 = lightbulb.number('stat_1', '1st stat on the scale', max_value=100, default=0)
    stat_2 = lightbulb.number('stat_2', '2nd stat on the scale', max_value=100, default=0)
    stat_3 = lightbulb.number('stat_3', '3rd stat on the scale', max_value=100, default=0)
    stat_4 = lightbulb.number('stat_4', '4th stat on the scale', max_value=100, default=0)
    stat_5 = lightbulb.number('stat_5', '5th stat on the scale', max_value=100, default=0)
    stat_6 = lightbulb.number('stat_6', '6th stat on the scale', max_value=100, default=0)
    stat_7 = lightbulb.number('stat_7', '7th stat on the scale', max_value=100, default=0)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        announcement_url = os.getenv('ANNOUNCEMENT_URL', 'https://discord.com/channels/...')
        recruitment_url = os.getenv('RECRUITMENT_URL', 'https://discord.com/channels/...')
        disabled_embed = hikari.Embed(title='Pricechecker Temporarily Disabled', description=f'For more information, read [Annoucement]({announcement_url}) in support server', color='#FFF000')
        info = f'Pricechecking functions are temporarily disabled until the market crowdsources data and full integration is complete.\n\nWe are looking for volunteers to participate in a ML approach to price estimation\nRead [here]({recruitment_url}) if interested\n'
        disabled_embed.add_field(name='Important Notice', value=info, inline=False)
        disabled_embed.set_footer(text='Nori Bot - Item Price Checker')
        await ctx.respond(embed=disabled_embed)

@items.register
class ItemPricecheck(lightbulb.SlashCommand, name='pricecheck', description='Auto price-checker with Encoded item (Mythic)'):
    item = lightbulb.string('item', 'In game item from Wynntils F3')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        import os
        announcement_url = os.getenv('ANNOUNCEMENT_URL', 'https://discord.com/channels/...')
        recruitment_url = os.getenv('RECRUITMENT_URL', 'https://discord.com/channels/...')
        disabled_embed = hikari.Embed(title='Pricechecker Temporarily Disabled', description=f'For more information, read [Annoucement]({announcement_url}) in support server', color='#FFF000')
        info = f'Pricechecking functions are temporarily disabled until the market crowdsources data and full integration is complete.\n\nWe are looking for volunteers to participate in a ML approach to price estimation\nRead [here]({recruitment_url}) if interested\n'
        disabled_embed.add_field(name='Important Notice', value=info, inline=False)
        disabled_embed.set_footer(text='Nori Bot - Item Price Checker')
        await ctx.respond(embed=disabled_embed)

@items.register
class ItemAutoWeigh(lightbulb.SlashCommand, name='weigh', description='Auto Weighing with Encoded Item (Mythic)'):
    item = lightbulb.string('item', 'In game item from Wynntils F3')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        initial_embed = hikari.Embed(title=f'Mythic weighing requested by {user}', description='Processing...', color='#9823F9')
        await ctx.respond(embed=initial_embed)
        try:
            from lib.decoders import ItemDecoder
            from lib.item_weight import item_weight_output, weigh_scale
        except Exception as error:
            error_embed = hikari.Embed(title='Item decoder is not ready', description=f'{type(error).__name__}: {error}', color='#9823F9')
            await ctx.edit_response(-1, embed=error_embed)
            return
        item_utils = _item_utils()
        item_string = self.item
        decoder = ItemDecoder()
        result = decoder.decode_item_string(item_string, config.item_map)
        if result:
            item_output = item_weight_output(item_string, config.item_map)
            if item_output:
                item_name = str(list(item_output.keys())[0])
                scales = item_output[item_name]
                if not scales:
                    error_embed = hikari.Embed(title=f'No available scale for {item_string}', description='Currently only support mythic-tier items', color='#9823F9')
                    await ctx.edit_response(-1, embed=error_embed)
                    return
                item_data = item_utils.item_search(item_name)
                try:
                    icon_id = item_data[2] if item_data else None
                except Exception as error:
                    icon_id = None
                    print(error)
                item_type = item_data[4] if item_data else None
                display = ''
                stats = result.stats
                rates = result.rates
                for stat_id, value in stats.items():
                    rate = rates.get(stat_id, 0)
                    stat_name = config.stat_mapping.get(stat_id, stat_id)
                    display += f'{value} {stat_name} [{rate}%]\n'
                web_page = f'**[Item Analysis](https://nori.fish/wynn/item/analysis/) & [#1 Ranked Mythics](https://nori.fish/wynn/item/mythic/)**'
                display_line = display
                weigh_embed = hikari.Embed(title=f'Auto Weight Evaluation', description=web_page, color='#9823F9')
                if result.shiny:
                    item_name = f'Shiny {item_name}'
                    display_line = f'*{result.shiny}*\n' + display_line
                weigh_embed.add_field(f'{item_name}', display_line)
                sorted_scales = dict(sorted(scales.items(), key=lambda item: item[1], reverse=True))
                for weight in sorted_scales:
                    overall = sorted_scales[weight]
                    weight_display = f'```json\nWeight: {overall}%```\n'
                    weigh_embed.add_field(f'{weight} Scale', weight_display)
                try:
                    if item_type in ['helmet', 'chestplate', 'leggings', 'boots']:
                        item_url = hikari.files.File(str(RESOURCES_PATH / f'{item_type}.png'))
                        weigh_embed.set_thumbnail(item_url)
                    elif icon_id:
                        item_url = f'https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp'
                        weigh_embed.set_thumbnail(item_url)
                except Exception as error:
                    print(error)
                    pass
                weigh_embed.set_footer('Nori Bot - Auto Mythic Weighing')
                await ctx.edit_response(-1, embed=weigh_embed)
            else:
                error_embed = hikari.Embed(title=f'No available scale for {item_string}', description='Currently only support mythic-tier items', color='#9823F9')
                await ctx.edit_response(-1, embed=error_embed)
        else:
            error_embed = hikari.Embed(title=f'Failed to decode {item_string}', description='Contact support server for any issue.', color='#9823F9')
            await ctx.edit_response(-1, embed=error_embed)

@items.register
class ItemScale(lightbulb.SlashCommand, name='scale', description='Weighing scale for mythic'):
    item = lightbulb.string('item', 'Item name (Mythic only)')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond('Loading mythic scale...', flags=hikari.MessageFlag.LOADING)
        from lib.item_weight import weigh_scale
        from lib.config import DATA_PATH
        item_name = self.item
        scale_data = weigh_scale(item_name, str(DATA_PATH / 'mythic_weights.json'))
        if scale_data:
            scales = scale_data[0]
            timestamp = scale_data[1]
            item_data = _item_utils().item_search(item_name)
            try:
                icon_id = item_data[2] if item_data else None
            except Exception as error:
                icon_id = None
                print(error)
            item_type = item_data[4] if item_data else None
            item = str(list(scales.keys())[0])
            all_scales = scales[item]
            web_page = f'[#1 Mythic & Scales on Nori-Web](https://nori.fish/wynn/item/mythic/)'
            scale_embed = hikari.Embed(title='Mythic Weight Scale', description=f'{web_page}\n### Result for {item}: {len(all_scales)} ###', color='#A300F0')
            for scale in all_scales:
                scale_embed.add_field(f'{scale}', all_scales[scale])
            try:
                if item_type in ['helmet', 'chestplate', 'leggings', 'boots']:
                    item_url = hikari.files.File(str(RESOURCES_PATH / f'{item_type}.png'))
                    scale_embed.set_thumbnail(item_url)
                elif icon_id:
                    item_url = f'https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp'
                    scale_embed.set_thumbnail(item_url)
            except Exception as error:
                print(error)
                pass
            scale_embed.add_field('Latest data update', f'<t:{timestamp}>')
            scale_embed.set_footer('Nori Bot - Mythic scale')
            await ctx.edit_response(-1, embed=scale_embed, content='')
        else:
            scale_embed = hikari.Embed(title=f'No available scale for {item_name}', color='#AEB1B1')
            await ctx.edit_response(-1, embed=scale_embed, content='')

@items.register
class ItemCheck(lightbulb.SlashCommand, name='check', description='Decode an item and display its IDs (All Items)'):
    item = lightbulb.string('item', 'In game item from Wynntils F3')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond('Decoding item...', flags=hikari.MessageFlag.LOADING)
        try:
            from lib.decoders import ItemDecoder
        except Exception as error:
            error_embed = hikari.Embed(title='Item decoder is not ready', description=f'{type(error).__name__}: {error}', color='#ACFFF2')
            await ctx.edit_response(-1, embed=error_embed, content='')
            return
        item_string = self.item
        decoder = ItemDecoder()
        result = decoder.decode_item_string(item_string, config.item_map)
        if result:
            name = result.name
            item_data = _item_utils().item_search(name)
            try:
                icon_id = item_data[2] if item_data else None
            except Exception as error:
                icon_id = None
                print(error)
            item_type = item_data[4] if item_data else None
            stats = result.stats
            rates = result.rates
            display = ''
            sum_rate = 0
            for stat_id, value in stats.items():
                rate = rates.get(stat_id, 0)
                display += f'{value} {config.stat_mapping.get(stat_id, stat_id)} [{rate}%]\n'
                sum_rate += float(rate)
            if not rates:
                await ctx.edit_response(-1, 'Invalid input, please copy the item in game properly.')
                return
            overall = round(sum_rate / len(rates), 1)
            web_page = f'[Item Analysis on Nori-Web](https://nori.fish/wynn/item/analysis/)'
            stats_embed = hikari.Embed(title='Item Stats', description=f'IDs decoded from Wynntils\n{web_page}', color='#C0FD5D')
            if result.shiny:
                name = f'Shiny {name}'
                display = f'*{result.shiny}*\n' + display
            stats_embed.add_field(f'{name} [{overall}%]\n', f'{display}')
            try:
                if item_type in ['helmet', 'chestplate', 'leggings', 'boots']:
                    item_url = hikari.files.File(str(RESOURCES_PATH / f'{item_type}.png'))
                    stats_embed.set_thumbnail(item_url)
                elif icon_id:
                    item_url = f'https://cdn.wynncraft.com/nextgen/itemguide/3.3/{icon_id}.webp'
                    stats_embed.set_thumbnail(item_url)
            except Exception as error:
                print(error)
                pass
            stats_embed.set_footer('Nori Bot - Item decoder')
            await ctx.edit_response(-1, embed=stats_embed, content='')
        else:
            await ctx.edit_response(-1, 'Invalid input, please copy the item in game properly.')

@items.register
class ItemSales(lightbulb.SlashCommand, name='sales', description='Submit item sales', hooks=[sales_contributor_only()]):
    item = lightbulb.string('item', 'Item name (Mythic only)')
    price = lightbulb.number('price', 'Price in stacks')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        import os
        import json
        from lib.config import sales_data, DATA_PATH
        item_name = self.item
        price = self.price
        user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        username = user.username
        if item_name not in sales_data:
            sales_data[item_name] = []
        sales_data[item_name].append({'price': price, 'seller': username, 'timestamp': int(time.time())})
        try:
            with open(DATA_PATH / 'sales_data.json', 'w') as file:
                json.dump(sales_data, file, indent=2)
            sales_embed = hikari.Embed(title='Sale Submitted', description=f'Thank you {username}!', color='#51FFCA')
            sales_embed.add_field(item_name, f'Price: {price} stacks')
            sales_embed.set_footer('Nori Bot - Sales Submission')
            await ctx.respond(embed=sales_embed)
        except Exception as error:
            print(f'Error saving sales data: {error}')
            await ctx.respond('Error saving sale data. Please contact support.')

@items.register
class ItemLootpool(lightbulb.SlashCommand, name='lootpool', description='Weekly Lootpool Rotation'):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond('Loading weekly lootpool...', flags=hikari.MessageFlag.LOADING)
        from lib.views.items import build_lootpool_embed, lootView
        from lib.config import lootpool_user
        lootpool_user[ctx.user.username] = 'Mythic'
        view = lootView(timeout=120)
        message = await ctx.edit_response(-1, embed=build_lootpool_embed('Mythic'), content='', components=view.build())
        ctx.client.app.d.miru.start_view(view, bind_to=message)
        await view.wait()

@items.register
class ItemHistory(lightbulb.SlashCommand, name='history', description='Find item in the lootpool history'):
    item = lightbulb.string('item', 'Item name')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond('Searching lootpool history...', flags=hikari.MessageFlag.LOADING)
        item_name = self.item
        item_data = _find_item_in_lootpool_history(item_name)
        total = 0
        total_shiny = 0
        last_seen = None
        last_region = None
        last_seen_shiny = None
        last_region_shiny = None
        last_tracker = None
        for week, data in item_data.items():
            if data['count'] > 0:
                total += data['count']
                last_seen = week
                last_region = ', '.join(data['region'])
            if data['shiny']:
                total_shiny += 1
                last_seen_shiny = week
                last_region_shiny = data['shiny_region']
                last_tracker = data['tracker']
        history_embed = hikari.Embed(title='Lootpool History Search', description=f'{item_name} has been recorded **{total}** times in historical data.\nIts shiny variant was recorded **{total_shiny}** times.', color='#4FE5F9')
        if last_seen:
            history_embed.add_field('Last Seen', f'Week of **{last_seen}** in *{last_region}*')
        else:
            history_embed.add_field('Last Seen', 'No history found.')
        if last_seen_shiny:
            history_embed.add_field('Shiny Version Last Seen', f'Week of **{last_seen_shiny}** in *{last_region_shiny}*\n**{last_tracker}**')
        else:
            history_embed.add_field('Shiny Version Last Seen', 'No shiny history found.')
        history_embed.set_thumbnail('https://static.wikia.nocookie.net/wynncraft_gamepedia_en/images/f/f0/LootrunUpdateIcon.png/revision/latest?cb=20230709013002')
        history_embed.set_footer('Nori Bot - Lootpool History')
        await ctx.edit_response(-1, embed=history_embed, content='')
loader.command(items)
