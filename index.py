"""
Author: Om Ghonasgi
Date: 2026-09-19
Module: index.py
Outside sources: Cursor with Claude Opus 4.7 Agent
Description: Entry point for the Minesweeper game. Wires together the game controller, reveal cascade, input, and display modules into a single terminal game loop.

Project 2 update (Arpa Das, 2026-10-05, Claude Code/Claude Sonnet 5 assisted):
added the sound_effects hook below so the custom sound-effects feature reacts
to moves. No existing game logic was changed; sound_effects.notify_move()
only reads a before/after snapshot that the loop already has.
"""

# imports from other modules made by the team members
import time

from display import render, render_message
from game import Game
from input_handler import get_mine_count, get_move, get_ai_difficulty, get_ai_mode
from reveal import RevealManager
from sound_effects import SoundEffects


# Map Game's internal state names to the user-facing status strings.
STATUS_LABEL = {
    "PLAYING": "Playing",
    "VICTORY": "Victory",
    "LOSS": "Game Over: Loss",
}
AI_MOVE_DELAY = 0.3  # seconds to wait between AI moves

def main() -> None:
    print("Welcome to Minesweeper!")

    # edge case for when the user quits before entering the mine count.
    mine_count = get_mine_count()
    if mine_count is None:
        # Player hit Ctrl+C / Ctrl+D at the mine-count prompt.
        print("Goodbye!")
        return
    ai_mode = get_ai_mode()
    if ai_mode is None:
        print("Goodbye!")
        return

    difficulty = None
    if ai_mode != "off":
        difficulty = get_ai_difficulty()
        if difficulty is None:
            print("Goodbye!")
            return

    game = Game()

    #Serom's project2 integration
    game.startGame(ai_mode, difficulty, mine_count)

    sound_effects = SoundEffects()

    # Game places mines itself on the first reveal. We still want the
    # cascade uncovering that RevealManager provides, so we pass its
    # reveal method as the reveal_func and flip its own first-reveal
    # flag so it doesn't try to place a second set of mines on top.
    reveal_manager = RevealManager(game.board, mine_count, game.mine_manager)

    def reveal_func(row: int, col: str) -> None:
        reveal_manager.first_reveal_done = True
        reveal_manager.reveal(row, col)

    last_mover = "player"

    # Game loop, runs by getting how many flags are left, rendering the board, and getting the action from the user.
    while game.state == "PLAYING":
        flags_left = (
            game.flag_manager.get_flags_remaining()
            if game.flag_manager is not None
            else mine_count
        )
        render(game.board, flags_left, STATUS_LABEL[game.state])

        # AI_only mode
        if ai_mode == "auto":
            state_before = game.state
            move = game.aiTurn(reveal_func=reveal_func)
            if move is None:
                render_message("AI has no valid moves left. You win!")
                break
            action, row, col = move
            render_message(f"AI ({game.difficulty}) plays" f"{action} on {col}{row + 1}.")
            cell_after = game.board.get_cell(row, col)
            sound_effects.notify_move(action, True, cell_after, state_before, game.state)
            last_mover = "ai"
            time.sleep(AI_MOVE_DELAY)
            continue

        #player turn
        action, row, col = get_move()
        if action == "quit":
            render_message("Thanks for playing!")
            sound_effects.wait_until_done()
            return

        # Snapshot used only by sound_effects.notify_move(); game logic
        # below is unchanged from before this feature was added.
        was_covered = game.board.get_cell(row, col).is_covered
        state_before = game.state

        #game.process_move(action, (row, col), mine_count, reveal_func=reveal_func)
        moved = game.playerTurn(action, (row, col), reveal_func=reveal_func)

        cell_after = game.board.get_cell(row, col)
        sound_effects.notify_move(action, was_covered, cell_after, state_before, game.state)
        if moved:
            last_mover = "player"

        #AI turn in interactive mode
        if (ai_mode == "interactive" and game.state == "PLAYING" and game.current_Turn == "ai"):
            flags_left = (
                game.flag_manager.get_flags_remaining()
                if game.flag_manager is not None
                else mine_count
            )
            render(game.board, flags_left, STATUS_LABEL[game.state])
            state_before = game.state
            move = game.aiTurn(reveal_func=reveal_func)
            if move is None:
                render_message("AI has no valid moves left. You win!")

                if game.current_turn == "ai":
                    game.switchTurn()
            else:
                ai_action, ai_row, ai_col = move
                render_message(f"AI ({game.difficulty}) plays" f"{ai_action} on {ai_col}{ai_row + 1}.")
                ai_cell = game.board.get_cell(ai_row, ai_col)
                sound_effects.notify_move(ai_action, True, ai_cell, state_before, game.state)
                last_mover = "ai"

    # Final board + terminal status.
    flags_left = (
        game.flag_manager.get_flags_remaining()
        if game.flag_manager is not None
        else mine_count
    )
    render(game.board, flags_left, STATUS_LABEL[game.state])
    if game.state == "VICTORY":
        if last_mover == "ai":
            render_message("AI won! All safe cells cleared.")
        else:
            render_message("You won! All safe cells cleared.")
    else:
        if last_mover == "ai":
            render_message("AI hit a mine. Better luck next time!")
        else:
            render_message("You hit a mine. Better luck next time!")
    # Let the win/mine clip finish before the process exits -- Sound.play()
    # is non-blocking, so without this the clip would get cut off here.
    sound_effects.wait_until_done()


# main loop
if __name__ == "__main__":
    main()
