"""
Author: RawFish
Description: 5x5 tic tac toe logic
"""

class GameViewFive(miru.View):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for position in range(1, 26):  
            style = hikari.ButtonStyle.SECONDARY
            row = (position - 1) // 5
            button = miru.Button(label=str(position), style=style, row=row)
            button.callback = functools.partial(self.button_callback, position, miru.Context)
            self.add_item(button)

    async def button_callback(self, position, button: miru.Button, ctx: miru.Context):
        username = ctx.user.username
        result = await self.button_handler(position=position, username=username)
        feedback_embed = hikari.Embed(title=result[0], color="#FFDB99")
        feedback_embed.add_field("Game Board", result[1])
        feedback_embed.set_footer("Nori Bot - Mini Game")
        if "won" in result[0] or "draw" in result[0]:
            await ctx.edit_response(embed=feedback_embed, components=[])
            self.stop()
        else:
            await ctx.edit_response(embed=feedback_embed)

    async def button_handler(self, position: int, username: str):
        game_record[username].append(position)
        position -= 1

        if username not in mini_game:
            mini_game[username] = [' '] * 25

        if self.is_illegal_move(position, username):
            feedback = "Choose an empty spot.\n"
            game_board_str = self.render_game_board(username)
            return feedback, game_board_str

        # Player's move
        mini_game[username][position] = "O"
        if self.check_win('O', username):
            return await self.handle_end_game(username, "Win")

        if all(spot != ' ' for spot in mini_game[username]) or self.is_forced_draw(mini_game[username]):
            return await self.handle_end_game(username, "Draw")

        # Computer's move
        computer_move_position = self.computer_move(username)
        if computer_move_position is not None:
            mini_game[username][computer_move_position] = 'X'
            if self.check_win('X', username):
                return await self.handle_end_game(username, "Loss")

        if all(spot != ' ' for spot in mini_game[username]) or self.is_forced_draw(mini_game[username]):
            return await self.handle_end_game(username, "Draw")

        return "Make your move", self.render_game_board(username)

    def computer_move(self, username):
        board = mini_game[username]
        total_moves = sum(1 for spot in board if spot != ' ')
        chance = random.random()

        move = self.find_blocking_move(board, username)
        if move is not None:
            mini_game["logic"][username].append("find block")
            return move

        if total_moves <= 4 and chance < 0.10:
            available_positions = [i for i, spot in enumerate(board) if spot == ' ']
            if available_positions:
                mini_game["logic"][username].append("random")
                return random.choice(available_positions)
        elif 4 < total_moves <= 10 and chance < 0.05:
            available_positions = [i for i, spot in enumerate(board) if spot == ' ']
            if available_positions:
                mini_game["logic"][username].append("random")
                return random.choice(available_positions)
        elif 10 < total_moves <= 16 and chance < 0.025:
            available_positions = [i for i, spot in enumerate(board) if spot == ' ']
            if available_positions:
                mini_game["logic"][username].append("random")
                return random.choice(available_positions)
        elif total_moves > 16 and chance < 0.01:
            available_positions = [i for i, spot in enumerate(board) if spot == ' ']
            if available_positions:
                mini_game["logic"][username].append("random")
                return random.choice(available_positions)

        move = self.find_blocking_move(board, username)
        if move is not None:
            mini_game["logic"][username].append("find block")
            return move

        move = self.find_winning_move(board, username)
        if move is not None:
            mini_game["logic"][username].append("find move")
            return move

        move = self.find_fork(board, username)
        if move is not None:
            mini_game["logic"][username].append("find fork")
            return move

        move = self.block_fork(board, username)
        if move is not None:
            mini_game["logic"][username].append("block fork")
            return move

        # move = self.block_pattern(board, username)
        # if move is not None:
        #     mini_game["logic"][username].append("pattern block")
        #     return move

        # Other strategic moves
        strategic_moves = [
            self.take_center,
            self.take_corner,
            self.take_side
        ]
        strategy = random.choice(strategic_moves)
        move = strategy(board, username)
        if move is not None:
            mini_game["logic"][username].append("strategic")
            return move

        # Fallback: take any available space
        mini_game["logic"][username].append("fallback")
        return self.take_any(board, username)

    def find_winning_move(self, board, username):
        # First, check for immediate win
        for condition in self.get_win_conditions():
            if self.is_winning_opportunity(board, condition, 'X'):
                for pos in condition:
                    if board[pos] == ' ':
                        return pos
        best_move = None
        highest_future_win_potential = 0
        for pos in range(25):
            if board[pos] == ' ':
                board[pos] = 'X'
                future_win_count = self.count_future_winning_opportunities(board, username, 'X')
                if future_win_count > highest_future_win_potential:
                    highest_future_win_potential = future_win_count
                    best_move = pos
                board[pos] = ' '

        return best_move if highest_future_win_potential > 0 else None

    def count_future_winning_opportunities(self, board, username, mark):
        win_count = 0

        for pos in range(25):
            if board[pos] == ' ':
                board[pos] = mark
                for condition in self.get_win_conditions():
                    if self.is_winning_opportunity(board, condition, mark):
                        win_count += 1
                board[pos] = ' '

        return win_count

    def is_winning_opportunity(self, board, condition, mark):
        marks_in_condition = sum(board[pos] == mark for pos in condition)
        empty_in_condition = sum(board[pos] == ' ' for pos in condition)
        # AI can win if there are 4 of its marks and 1 empty spot in the condition
        return marks_in_condition == 4 and empty_in_condition == 1

    def block_pattern(self, board, username):
        known_patterns = [
            [13, 12, 11, 4, 9, 18, 17, 16, 14, 19, 24]
        ]
        for pattern in known_patterns:
            player_positions = [pos for pos in pattern if board[pos] == 'O']
            empty_positions = [pos for pos in pattern if board[pos] == ' ']

            if len(player_positions) >= 3:
                if empty_positions:
                    return random.choice(empty_positions)
        return None

    def find_fork(self, board, username):
        return self.search_for_fork(board, 'X', username)

    def find_blocking_move(self, board, username):
        # Check for immediate block
        for condition in self.get_win_conditions():
            if self.is_winning_opportunity(board, condition, 'O'):
                for pos in condition:
                    if board[pos] == ' ':
                        return pos
    
        # Plan to block in two steps
        return self.plan_two_step_blocking(board, username, 'O')
    
    def plan_two_step_blocking(self, board, username, opponent_mark):
        best_block = None
        highest_threat_prevented = 0
    
        for pos in range(25):
            if board[pos] == ' ':
                board[pos] = opponent_mark
                future_threats = self.count_future_winning_opportunities(board, username, opponent_mark)
    
                if future_threats > highest_threat_prevented:
                    highest_threat_prevented = future_threats
                    best_block = pos
    
                board[pos] = ' '  # Reset the board
    
        return best_block if highest_threat_prevented > 0 else None

    def block_fork(self, board, username):
        # First, check for immediate fork to block
        immediate_fork_block = self.search_for_fork(board, 'O', username)
        if immediate_fork_block is not None:
            return immediate_fork_block
    
        # Plan to block forks in two steps
        return self.plan_two_step_blocking(board, username, 'O')

    def find_blocking_move(self, board, username):
        # Check for immediate block
        for condition in self.get_win_conditions():
            if self.is_winning_opportunity(board, condition, 'O'):
                for pos in condition:
                    if board[pos] == ' ':
                        return pos
        return None

    def block_fork(self, board, username):
        # Check for immediate fork to block
        return self.search_for_fork(board, 'O', username)

    def search_for_fork(self, board, mark, username):
        for i in range(25):
            if board[i] == ' ':
                board[i] = mark
                if self.count_winning_moves(board, mark, username) >= 2:
                    board[i] = ' '
                    return i
                board[i] = ' '
        return None

    def count_winning_moves(self, board, mark, username):
        win_conditions = self.get_win_conditions()
        winning_moves = 0

        for condition in win_conditions:
            if self.is_potential_win(board, condition, mark):
                winning_moves += 1

        return winning_moves

    def is_potential_win(self, board, condition, mark):
        marks_in_condition = sum(board[pos] == mark for pos in condition)
        empty_in_condition = sum(board[pos] == ' ' for pos in condition)
        return marks_in_condition == 4 and empty_in_condition == 1

    def take_center(self, board, username):
        center = 12
        if board[center] == ' ':
            return center
        return None

    def take_corner(self, board, username):
        corners = [0, 4, 20, 24]
        for corner in corners:
            if board[corner] == ' ':
                return corner
        return None

    def take_side(self, board, username):
        sides = [i for i in range(25) if i not in [0, 4, 20, 24, 12]]  # Excluding corners and center
        for side in sides:
            if board[side] == ' ':
                return side
        return None

    def take_any(self, board, username):
        available_positions = [i for i, spot in enumerate(board) if spot == ' ']
        if available_positions:
            return random.choice(available_positions)
        return None

    def find_strategic_move(self, board, mark, username):
        for i in range(25):
            if board[i] == ' ':
                board[i] = mark
                if self.check_win(mark, username):
                    return i
                board[i] = ' '
        return None

    def check_win(self, player_mark, username):
        win_conditions = self.get_win_conditions()
        return any(all(mini_game[username][pos] == player_mark for pos in condition) for condition in win_conditions)

    def is_illegal_move(self, position: int, username: str):
        return mini_game[username][position] != ' '

    def get_win_conditions(self):
        win_conditions = []
        for i in range(5):
            horizontal = [j + i * 5 for j in range(5)]
            vertical = [i + j * 5 for j in range(5)]
            win_conditions.append(horizontal)
            win_conditions.append(vertical)

        diagonal1 = [i * 6 for i in range(5)]
        diagonal2 = [4 * i for i in range(1, 6)]
        win_conditions.append(diagonal1)
        win_conditions.append(diagonal2)

        return win_conditions

    def is_forced_draw(self, board):
        if all(spot != ' ' for spot in board):
            return True  # It's a draw if the board is full

        # Check if there are win conditions still achievable for either player
        for condition in self.get_win_conditions():
            if self.is_condition_achievable(board, condition, 'X') or \
                    self.is_condition_achievable(board, condition, 'O'):
                return False  # There's still a chance for a win

        return True  # No win conditions achievable, it's a draw

    def is_condition_achievable(self, board, condition, mark):
        """Check if a win condition is still achievable for a given mark."""
        opponent_mark = 'O' if mark == 'X' else 'X'
        return not any(board[pos] == opponent_mark for pos in condition)

    async def handle_end_game(self, username, outcome):
        if outcome == "Win":
            feedback = f"You won the game"
        elif outcome == "Loss":
            feedback = f"Bot won the game"
        else:
            feedback = f"It's a draw"
        game_board_str = self.render_game_board(username)
        game_record[username].append(outcome)
        game_record["5x5"][username].append(game_record[username])
        result = f"`{username}`: {game_record['5x5'][username][-1]}\n{mini_game[username]}\n{mini_game['logic'][username]}"
        print(result)
        await bot.rest.create_message(channel=1174901561282023424, content=result)
        self.stop()
        return feedback, game_board_str

    def render_game_board(self, username):
        board = mini_game[username]  
        lines = []
        for i in range(0, 25, 5):
            line = f' {board[i]} ║ {board[i + 1]} ║ {board[i + 2]} ║ {board[i + 3]} ║ {board[i + 4]} '
            lines.append(line)

        game_board_str = (
            "```"
            "╔═══╦═══╦═══╦═══╦═══╗\n"
            f"║{lines[0]}║\n"
            "╠═══╬═══╬═══╬═══╬═══╣\n"
            f"║{lines[1]}║\n"
            "╠═══╬═══╬═══╬═══╬═══╣\n"
            f"║{lines[2]}║\n"
            "╠═══╬═══╬═══╬═══╬═══╣\n"
            f"║{lines[3]}║\n"
            "╠═══╬═══╬═══╬═══╬═══╣\n"
            f"║{lines[4]}║\n"
            "╚═══╩═══╩═══╩═══╩═══╝"
            "```"
        )
        return game_board_str
