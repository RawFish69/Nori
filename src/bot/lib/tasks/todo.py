"""Reminder task loop."""

import asyncio
import time

import hikari

import lib.config as config


async def reminder_task(bot: hikari.GatewayBot, interval: int = 60):
    """Send due reminders created by `/do`."""
    print(f"Bot deployed in {config.MODE} mode\nReminder task interval: {interval} seconds")
    while True:
        try:
            if config.all_tasks:
                current_time = time.time()
                next_task_id = min(config.all_tasks, key=lambda key: config.all_tasks[key]["time"])
                next_task_time = config.all_tasks[next_task_id]["time"]
                wait_seconds = next_task_time - current_time
                if wait_seconds > 0:
                    await asyncio.sleep(wait_seconds)

                task_data = config.all_tasks.get(next_task_id)
                if task_data:
                    task_name = task_data["task"]
                    channel = task_data["channel"]
                    user_id = task_data["user_id"]
                    user = await bot.rest.fetch_user(user_id)
                    await bot.rest.create_message(
                        channel=channel,
                        content=f"\n{user.mention} **{task_name}**",
                        user_mentions=True,
                    )
                    del config.all_tasks[next_task_id]
                    print(f"Execute Task {task_name} Successfully.")
        except Exception as error:
            print(f"Reminder task error: {error}")

        await asyncio.sleep(interval)
