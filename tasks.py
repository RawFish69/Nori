# Sample code of TO-DO List function

all_tasks = {}
task_index = 1


@bot.command()
@lightbulb.option("timer", "Timer in hours")
@lightbulb.option("task", "Task name")
@lightbulb.command("do", "Add to to-do list")
@lightbulb.implements(lightbulb.SlashCommand)
async def todo_set(ctx):
    global task_index
    global all_tasks
    user = ctx.user.id
    user_name = await bot.rest.fetch_user(ctx.user.id)
    timer_s = float(ctx.options.timer) * 3600
    timer = timedelta(seconds=int(timer_s))
    todo_time = datetime.now() + timer
    task_name = ctx.options.task
    task_id = str(task_index)
    all_tasks.update({task_id: {}})
    all_tasks[task_id]["task"] = task_name
    all_tasks[task_id]["time"] = todo_time
    all_tasks[task_id]["user_name"] = user_name
    all_tasks[task_id]["channel"] = ctx.channel_id
    task_index += 1
    await ctx.respond(f"{user_name.mention} todo: **{task_name}** in {ctx.options.timer} hours or {int(timer_s/60)} minutes")
    print(all_tasks)


@bot.command()
@lightbulb.command("todo", "List of todos")
@lightbulb.implements(lightbulb.SlashCommand)
async def todo_list(ctx):
    todo_list = ""
    for task_id, task_info in all_tasks.items():
        task_name = task_info["task"]
        todo_time = task_info["time"]
        username = task_info["user_name"]
        time_left = todo_time - datetime.now()
        hours, remainder = divmod(time_left.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        todo_list += f"{task_id}. {username}: **{task_name}** - {hours}h {minutes}m {seconds}s\n"
    await ctx.respond(f"To-Do List:\n{todo_list}")


async def todo():
    print('Begin cycle')
    count = 0
    interval = 60
    while True:
        current_time = datetime.now()
        for id in all_tasks.copy():
            time = all_tasks[id]["time"]
            if time <= current_time:
                task = all_tasks[id]["task"]
                channel = all_tasks[id]["channel"]
                username = all_tasks[id]["user_name"]
                await bot.rest.create_message(channel=channel, content=f"{username.mention} {task}")
                del all_tasks[id]
                print("Executed")
        await asyncio.sleep(interval)
        count += 1
        print(f"Scan cycle - {count} | {count*interval} seconds elapsed since launch")


@bot.listen()
async def start_scan(event: hikari.StartingEvent):
    asyncio.create_task(todo())
    
