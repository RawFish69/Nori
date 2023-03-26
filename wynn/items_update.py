def item_update():
    category = 'all'
    request_data = requests.get(f'https://api.wynncraft.com/public_api.php?action=itemDB&category={category}')
    item_data = request_data.json()
    items = json.dumps(item_data, indent=3)
    with open('update_items.json', 'w') as file:
        file.write(items)
    item_names_old = []
    item_names_new = []
    with open("wynn_items.json", 'r') as f1, open("update_items.json", 'r') as f2:
        old_items_raw = json.load(f1)
        old_items_list = old_items_raw['items']
        new_items_raw = json.load(f2)
        new_items_list = new_items_raw['items']
    for item in old_items_list:
        item_names_old.append(item.get("name"))
    for item in new_items_list:
        item_names_new.append(item.get("name"))
    # Check for added
    # print(len(old_items_list), len(new_items_list))
    items_added = []
    items_removed = []
    for name in item_names_old:
        if name not in item_names_new:
            items_removed.append(name)
    for name in item_names_new:
        if name not in item_names_old:
            items_added.append(name)
    items_modified = [x for x in item_names_new if x in item_names_old]
    item_changelog = ""
    time_now = datetime.now()
    current_datetime = time_now.strftime("%Y-%m-%d %H:%M:%S")
    item_changelog += f"Item changelog - Updated from API\n"
    item_changelog += f"{len(new_items_list)} total items scanned\n"
    modified_count = 0
    # Only the items that were changed
    modified_log = ""
    temp_dict = {}
    val = old_items_list
    for new, old in zip(new_items_list, old_items_list):
        item_name = new["name"]
        if item_name in items_modified:
            # Same position
            if new != old and item_name == old["name"]:
                modified_count += 1
                modified_log += f"{item_name}:\n"
                for (new_stat, new_id), (old_stat, old_id) in zip(new.items(), old.items()):
                    if new_id != old_id:
                        modified_log += f"{new_stat}: {old_id} -> {new_id}\n"
                modified_log += "\n"
            # Moved position
            elif item_name != old["name"]:
                for old_item in old_items_list:
                    if item_name == old_item["name"] and new != old_item:
                        modified_count += 1
                        modified_log += f"{item_name}:\n"
                        for (stat_new, id_new), (stat_old, id_old) in zip(new.items(), old_item.items()):
                            if id_new != id_old:
                                modified_log += f"{stat_new}: {id_old} -> {id_new}\n"
                        modified_log += "\n"
    item_changelog += f"New Items: {len(items_added)}, Items Removed: {len(items_removed)}, Items changed: {modified_count}\n"
    item_changelog += f"Item Changes: \n{modified_log}"
    item_changelog += f"Items Added:\n"
    for item in items_added:
        item_changelog += f"- {item}\n"
    item_changelog += f"Removed Items:\n"
    for item in items_removed:
        item_changelog += f"- {item}\n"
    item_changelog += "\n"
    item_changelog += f"Log Update Date: {current_datetime}"
    # Write to the log file
    with open("item_change.log", 'w', encoding="utf-8") as log:
        log.write(item_changelog)
    print(item_changelog)
    with open("wynn_items.json", 'w') as f:
        f.write(json.dumps(new_items_raw, indent=4))
