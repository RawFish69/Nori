# Sample code of TO-DO List function

@bot.command()
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("todo", "List of todos (Owner)")
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
    todo_embed = hikari.Embed(title="To Do List", color="#00AEC0")
    todo_embed.add_field(f"{len(all_tasks)} Tasks Loaded:", f"{todo_list}")
    todo_embed.set_footer("Nori Bot - Task manager")
    await ctx.respond(todo_embed)

@bot.listen()
async def start_scan(event: hikari.StartingEvent):
    asyncio.create_task(todo())

