"""Owner task/reminder commands."""

import asyncio
import time

import hikari
import lightbulb

import lib.config as config
from lib.utils import check_user_access
from lib.manager_registry import get_managers
from lib.tasks.todo import reminder_task


def load_task_commands(bot: lightbulb.BotApp, blocked_users: list = None):
    """Load task/reminder commands."""

    @bot.listen(hikari.StartedEvent)
    async def _start_task_worker(event: hikari.StartedEvent):
        managers = get_managers()
        if not managers.get("task_worker_started"):
            managers["task_worker_started"] = True
            asyncio.create_task(reminder_task(bot))

    @bot.command()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("user", "Target user ID", required=False, type=hikari.User)
    @lightbulb.option("timer", "Timer in hours")
    @lightbulb.option("task", "Task name")
    @lightbulb.command("do", "Add to to-do list (Owner)")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def todo_set(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)

        target_user = ctx.options.user if ctx.options.user else await bot.rest.fetch_user(ctx.user.id)
        if isinstance(target_user, hikari.User):
            user_obj = target_user
        else:
            user_obj = await bot.rest.fetch_user(target_user)

        timer_seconds = float(ctx.options.timer) * 3600
        todo_time = int(time.time()) + timer_seconds
        task_id = str(config.task_index)

        config.all_tasks[task_id] = {
            "task": ctx.options.task,
            "time": todo_time,
            "user_id": user_obj.id,
            "channel": ctx.channel_id,
        }
        config.task_index += 1
        await ctx.respond(f"`{user_obj}`: **{ctx.options.task}** <t:{int(todo_time)}:R>")

    @bot.command()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.command("todo", "List of todos (Owner)")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def todo_list(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        if not config.all_tasks:
            await ctx.respond("No tasks loaded.")
            return

        lines = []
        for task_id, task_info in config.all_tasks.items():
            username = await bot.rest.fetch_user(task_info["user_id"])
            lines.append(f"{task_id}. {username}: **{task_info['task']}** - <t:{int(task_info['time'])}:R>")

        todo_embed = hikari.Embed(title="To Do List", color="#00AEC0")
        todo_embed.add_field(f"{len(config.all_tasks)} Tasks Loaded:", "\n".join(lines))
        todo_embed.set_footer("Nori Bot - Task manager")
        await ctx.respond(todo_embed)

    @bot.command()
    @lightbulb.add_checks(lightbulb.owner_only)
    @lightbulb.option("index", "Action")
    @lightbulb.command("cleartask", "Remove a task on the To-Do list")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def cleartask(ctx: lightbulb.Context):
        await check_user_access(ctx, blocked_users)
        task_option = str(ctx.options.index)

        if "all" in task_option.lower():
            config.all_tasks.clear()
            config.task_index = 1
            await ctx.respond("All tasks cleared.")
            return

        if task_option in config.all_tasks:
            config.all_tasks.pop(task_option)
            await ctx.respond(f"Task #{task_option} has been cleared.")
            return

        await ctx.respond("Invalid input.")
