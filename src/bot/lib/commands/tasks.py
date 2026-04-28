"""Owner task/reminder commands."""
import asyncio
import time
import hikari
import lightbulb
import lib.config as config
from lib.manager_registry import get_managers
from lib.tasks.todo import reminder_task
loader = lightbulb.Loader()

@loader.listener(hikari.StartedEvent)
async def _start_task_worker(event: hikari.StartedEvent):
    managers = get_managers()
    if not managers.get('task_worker_started'):
        managers['task_worker_started'] = True
        asyncio.create_task(reminder_task(event.app))

@loader.command
class TodoSet(lightbulb.SlashCommand, name='do', description='Add to to-do list (Owner)', hooks=[lightbulb.prefab.owner_only]):
    task = lightbulb.string('task', 'Task name')
    timer = lightbulb.string('timer', 'Timer in hours')
    user = lightbulb.user('user', 'Target user ID', default=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        target_user = self.user if self.user else await ctx.client.app.rest.fetch_user(ctx.user.id)
        if isinstance(target_user, hikari.User):
            user_obj = target_user
        else:
            user_obj = await ctx.client.app.rest.fetch_user(target_user)
        timer_seconds = float(self.timer) * 3600
        todo_time = int(time.time()) + timer_seconds
        task_id = str(config.task_index)
        config.all_tasks[task_id] = {'task': self.task, 'time': todo_time, 'user_id': user_obj.id, 'channel': ctx.channel_id}
        config.task_index += 1
        await ctx.respond(f'`{user_obj}`: **{self.task}** <t:{int(todo_time)}:R>')

@loader.command
class TodoList(lightbulb.SlashCommand, name='todo', description='List of todos (Owner)', hooks=[lightbulb.prefab.owner_only]):

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        if not config.all_tasks:
            await ctx.respond('No tasks loaded.')
            return
        lines = []
        for task_id, task_info in config.all_tasks.items():
            username = await ctx.client.app.rest.fetch_user(task_info['user_id'])
            lines.append(f"{task_id}. {username}: **{task_info['task']}** - <t:{int(task_info['time'])}:R>")
        todo_embed = hikari.Embed(title='To Do List', color='#00AEC0')
        todo_embed.add_field(f'{len(config.all_tasks)} Tasks Loaded:', '\n'.join(lines))
        todo_embed.set_footer('Nori Bot - Task manager')
        await ctx.respond(todo_embed)

@loader.command
class Cleartask(lightbulb.SlashCommand, name='cleartask', description='Remove a task on the To-Do list', hooks=[lightbulb.prefab.owner_only]):
    index = lightbulb.string('index', 'Action')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        task_option = str(self.index)
        if 'all' in task_option.lower():
            config.all_tasks.clear()
            config.task_index = 1
            await ctx.respond('All tasks cleared.')
            return
        if task_option in config.all_tasks:
            config.all_tasks.pop(task_option)
            await ctx.respond(f'Task #{task_option} has been cleared.')
            return
        await ctx.respond('Invalid input.')
