# Previous code from nori-bot main

@bot.listen()
async def start_scan(event: hikari.StartingEvent):
    global deploy_time, lootpool_data, lootpool_history
    deploy_time = time.time()
    # Texas CST Timezone (UTC-6) or (UTC-5)
    CST = timezone(timedelta(hours=-5))
    time_now = datetime.now(CST)
    current_datetime = time_now.strftime("%Y-%m-%d %H:%M:%S")
    # Load config and data files
    # ...

    # Create tasks
    asyncio.create_task(todo())

async def todo():
    interval = 60 # Every minute
    while True:
        if all_tasks:
            current_time = time.time()
            next_task_id = min(all_tasks, key=lambda id: all_tasks[id]["time"])
            next_task_time = all_tasks[next_task_id]["time"]
            time_to_next_task = next_task_time - current_time
            if time_to_next_task > 0:
                await asyncio.sleep(time_to_next_task)
            task = all_tasks[next_task_id]["task"]
            channel = all_tasks[next_task_id]["channel"]
            username = all_tasks[next_task_id]["user_name"]
            await bot.rest.create_message(channel=channel, content=f"\n{username.mention} **{task}**",
                                          user_mentions=True)
            del all_tasks[next_task_id]
            print(f"Execute Task {task} Successfully.")
        await asyncio.sleep(interval)

