import requests
import re
from items import item_search

class ItemDecoder:
    def __init__(self):
        self.stat_order_url = "https://raw.githubusercontent.com/RawFish69/Nori/main/data/mythic_weights.json"
        self.stat_order = self.fetch_stat_order()

    def fetch_stat_order(self):
        api_data = requests.get(self.stat_order_url)
        return api_data.json()["order"]

    def decode_gear_item(self, encoded_string):
        # Current wynntils blocker format 
        # Update once artemis makes any changes
        START = "\U000F5FF0"
        END = "\U000F5FF1"
        SEPARATOR = "\U000F5FF2"
        RANGE_PATTERN = "[" + "\U000F5000" + "-" + "\U000F5F00" + "]"
        OFFSET = 0xF5000

        encoded_pattern = re.compile(
            START + "(?P<Name>.+?)" + SEPARATOR + "(?P<Ids>"
            + RANGE_PATTERN + "+)(?:" + SEPARATOR + "(?P<Powders>" + RANGE_PATTERN + "+))?(?P<Rerolls>" + RANGE_PATTERN + "+)" + END
        )

        def decode_numbers(text):
            return [ord(text[i]) - OFFSET for i in range(len(text))]

        match = encoded_pattern.match(encoded_string)
        if not match:
            return None

        name = match.group("Name")
        ids = decode_numbers(match.group("Ids"))
        powders = decode_numbers(match.group("Powders")) if match.group("Powders") else []
        rerolls = decode_numbers(match.group("Rerolls")) if match.group("Rerolls") else []

        return {
            "name": name,
            "identifications": ids,
            "powders": powders,
            "rerolls": rerolls
        }

    def decode_item(self, item_string):
        stat_order = self.stat_order
        decoded_item = self.decode_gear_item(item_string)
        if not decoded_item:
            return None
        name = decoded_item['name']
        ids = decoded_item['identifications']
        api_stats = self.item_search(name)[1]
        stat_sorted = {name: {}, "rate": {}}
        index = 0
        for tils_stat in stat_order:
            if tils_stat not in api_stats or index >= len(ids):
                continue
            baseValue = api_stats[tils_stat]
            id_max = baseValue * 1.3
            id_min = baseValue * 0.3 if baseValue >= 0 else baseValue * 1.3
            id_max = baseValue * 0.3 if baseValue < 0 else id_max
            encoded_value = ids[index] // 4
            Actual_ID = ((encoded_value + 30) / 100) * baseValue if abs(baseValue) > 100 else encoded_value + id_min
            percentage = ((Actual_ID - id_min) / (id_max - id_min)) * 100
            stat_sorted[name].update({tils_stat: round(Actual_ID, 2)})
            stat_sorted["rate"].update({tils_stat: min(max(round(percentage, 1), 0), 100)})
            index += 1
        return stat_sorted








