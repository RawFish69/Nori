"""Mini-game commands."""
import random
import hikari
import lightbulb
import miru
from lib.config import deploy_time, game_record
from lib.lightbulb_compat import lb_choices
loader = lightbulb.Loader()

class TicTacToeView(miru.View):

    def __init__(self, user_id: int, username: str, mode: str, size: int, timeout: float=180):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.username = username
        self.mode = mode
        self.size = size
        self.board = [' '] * (size * size)
        self.moves = []
        for position in range(1, size * size + 1):
            row = (position - 1) // size
            button = miru.Button(label=str(position), style=hikari.ButtonStyle.SECONDARY, row=row)
            button.callback = self._button_callback_factory(position)
            self.add_item(button)

    def _win_conditions(self):
        n = self.size
        rows = [[r * n + c for c in range(n)] for r in range(n)]
        cols = [[r + c * n for c in range(n)] for r in range(n)]
        diag_1 = [i * (n + 1) for i in range(n)]
        diag_2 = [(i + 1) * (n - 1) for i in range(n)]
        return rows + cols + [diag_1, diag_2]

    def check_win(self, mark: str):
        return any((all((self.board[pos] == mark for pos in condition)) for condition in self._win_conditions()))

    def is_draw(self):
        return all((spot != ' ' for spot in self.board))

    def render_board(self):
        n = self.size
        lines = []
        for row in range(n):
            start = row * n
            row_data = self.board[start:start + n]
            lines.append(' | '.join([cell if cell != ' ' else '.' for cell in row_data]))
        return '```text\n' + '\n'.join(lines) + '\n```'

    def game_embed(self, title: str):
        embed = hikari.Embed(title=title, color='#FFDB99')
        embed.add_field('Game Board', self.render_board())
        embed.set_footer('Nori Bot - Mini Game')
        return embed

    def computer_move(self):
        empty_positions = [index for index, spot in enumerate(self.board) if spot == ' ']
        if not empty_positions:
            return None
        for pos in empty_positions:
            self.board[pos] = 'X'
            if self.check_win('X'):
                self.board[pos] = ' '
                return pos
            self.board[pos] = ' '
        for pos in empty_positions:
            self.board[pos] = 'O'
            if self.check_win('O'):
                self.board[pos] = ' '
                return pos
            self.board[pos] = ' '
        center = len(self.board) // 2
        if center in empty_positions:
            return center
        return random.choice(empty_positions)

    def _store_result(self, outcome: str):
        if self.username not in game_record[self.mode]:
            game_record[self.mode][self.username] = []
        session = self.moves + [outcome]
        game_record[self.mode][self.username].append(session)

    def _button_callback_factory(self, position: int):

        async def callback(ctx: miru.ViewContext) -> None:
            await self._button_callback(position, ctx)
        return callback

    async def _button_callback(self, position: int, ctx: miru.ViewContext):
        if ctx.user.id != self.user_id:
            await ctx.respond('This game belongs to another user.', flags=hikari.MessageFlag.EPHEMERAL)
            return
        board_pos = position - 1
        if self.board[board_pos] != ' ':
            await ctx.edit_response(embed=self.game_embed('Choose an empty spot.'))
            return
        self.board[board_pos] = 'O'
        self.moves.append(position)
        if self.check_win('O'):
            self._store_result('Win')
            await ctx.edit_response(embed=self.game_embed('You won the game'), components=[])
            self.stop()
            return
        if self.is_draw():
            self._store_result('Draw')
            await ctx.edit_response(embed=self.game_embed("It's a draw"), components=[])
            self.stop()
            return
        bot_move = self.computer_move()
        if bot_move is not None:
            self.board[bot_move] = 'X'
        if self.check_win('X'):
            self._store_result('Loss')
            await ctx.edit_response(embed=self.game_embed('Bot won the game'), components=[])
            self.stop()
            return
        if self.is_draw():
            self._store_result('Draw')
            await ctx.edit_response(embed=self.game_embed("It's a draw"), components=[])
            self.stop()
            return
        await ctx.edit_response(embed=self.game_embed('Make your move'))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(components=self.build())
        except Exception as error:
            print(f'Failed to edit message on timeout: {error}')

def _resolve_target_user(user):
    if isinstance(user, hikari.User):
        return user
    return None
minigames = lightbulb.Group('game', 'Nori Mini Games')

@minigames.register
class GameTtt(lightbulb.SlashCommand, name='tictactoe', description='Play Tic Tac Toe'):
    mode = lightbulb.string('mode', 'Choose a game mode', choices=lb_choices(['3x3', '4x4', '5x5']), default='5x5')

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        username = ctx.user.username
        mode = self.mode if self.mode in {'3x3', '4x4', '5x5'} else '5x5'
        size = int(mode[0])
        if username not in game_record[mode]:
            game_record[mode][username] = []
        view = TicTacToeView(user_id=ctx.user.id, username=username, mode=mode, size=size, timeout=180)
        first_mover = random.choice(['player', 'computer'])
        if first_mover == 'computer':
            bot_pos = view.computer_move()
            if bot_pos is not None:
                view.board[bot_pos] = 'X'
        start_embed = hikari.Embed(title='Mini Game - Tic Tac Toe', description='Player - O, Bot - X', color='#FFDB99')
        start_embed.add_field('Make Your Move', view.render_board())
        start_embed.add_field('First Move', 'Bot made the first move' if first_mover == 'computer' else "It's your turn")
        start_embed.set_footer('Nori Bot - Mini Game')
        message = await ctx.respond(embed=start_embed, components=view.build())
        message = await ctx.fetch_response(message)
        ctx.client.app.d.miru.start_view(view, bind_to=message)
        await view.wait()

@minigames.register
class PlayerRecord(lightbulb.SlashCommand, name='record', description='Mini Game Record'):
    user = lightbulb.user('user', 'specific user', default=None)

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        target_user = _resolve_target_user(self.user)
        if target_user is None:
            target_user = await ctx.client.app.rest.fetch_user(ctx.user.id)
        username = target_user.username
        record_embed = hikari.Embed(title=f'{username} Player Card', description=f'Session started <t:{int(deploy_time)}:R>', color='#FFDB99')
        found_any = False
        for mode in ['3x3', '4x4', '5x5']:
            if username in game_record[mode]:
                wins = 0
                losses = 0
                draws = 0
                for game in game_record[mode][username]:
                    if game and game[-1] == 'Win':
                        wins += 1
                    elif game and game[-1] == 'Loss':
                        losses += 1
                    elif game and game[-1] == 'Draw':
                        draws += 1
                record_embed.add_field(f'Tic Tac Toe [{mode}]', f'**{wins}** Wins / **{losses}** Loss / **{draws}** Draws')
                found_any = True
        if not found_any:
            record_embed.add_field('No record this session', 'Play a game with `/game tictactoe`')
        avatar_url = target_user.make_avatar_url()
        if avatar_url:
            record_embed.set_thumbnail(avatar_url)
        record_embed.set_footer('Nori Bot - Mini Game')
        await ctx.respond(record_embed)
loader.command(minigames)
