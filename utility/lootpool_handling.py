# Previous code from Lootpool functions

async def estimate_week_number():
    current_time = int(time.time())
    elapsed_time = current_time - first_week_timestamp
    elapsed_weeks = elapsed_time / seconds_per_week
    week_number = int(elapsed_weeks) + 1
    return week_number


async def create_weekly_lootpool():
    week = await estimate_week_number()
    starting_time = (week - 1) * seconds_per_week + first_week_timestamp
    lootpool = {
        "Loot": {
            region: {
                "Shiny": lootpool_data[region]["Shiny"],
                "Mythic": lootpool_data[region]["Mythic"],
                "Fabled": lootpool_data[region]["Fabled"],
                "Legendary": lootpool_data[region]["Legendary"],
                "Rare": lootpool_data[region]["Rare"],
                "Unique": lootpool_data[region]["Unique"]
            }
            for region in ["SE", "Corkus", "Sky", "Molten"]
        },
        "Timestamp": starting_time
    }
    return lootpool


async def update_lootpool(weekly_lootpool):
    with open("/home/ubuntu/nori-bot/data/weekly_lootpool.json", "w") as file:
        json.dump(weekly_lootpool, file, indent=3)
    print(json.dumps(weekly_lootpool, indent=3))
    print(f"\nFile updated\nTimestamp: {weekly_lootpool['Timestamp']}")


async def history_log(weekly_lootpool, update: bool, date):
    if update is True:
        log_data = f"Week of {date}:\n"
        for region, pool in weekly_lootpool["Loot"].items():
            log_data += f"{region}:\nShiny {pool['Shiny']['Item']}\n{pool['Shiny']['Tracker']} Tracker\n"
            for mythic in pool["Mythic"]:
                log_data += f"- {mythic}\n"
        log_data += "\n"
        with open("/home/ubuntu/nori-bot/data/lootpool_history.log", "a") as file:
            file.write(log_data)
        print(log_data)
        return log_data
