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

Project 2 update (AI solver): the loop now asks how the AI should take part.
"Off" plays exactly as before, "interactive" alternates player and AI turns,
and "auto" lets the AI solve the board on its own. The AI shares the player's
Board, so neither side gets a different game.
"""

# imports from other modules made by the team members
import time

from ai_solver import AISolver
from display import render, render_message
from game import Game
from input_handler import get_ai_difficulty, get_ai_mode, get_mine_count, get_move
from reveal import RevealManager
from sound_effects import SoundEffects


# Map Game's internal state names to the user-facing status strings.
STATUS_LABEL = {
    "PLAYING": "Playing",
    "VICTORY": "Victory",
    "LOSS": "Game Over: Loss",
}

# Pause between automatic AI moves so the board stays readable.
AI_MOVE_DELAY = 0.35


def flags_left(game: Game, mine_count: int) -> int:
    """Flags the player still has; the full count until the first reveal."""
    if game.flag_manager is None:
        return mine_count
    return game.flag_manager.get_flags_remaining()


def cell_label(row: int, col: str) -> str:
    """Turn (4, "D") back into the "D5" the player sees."""
    return f"{col}{row + 1}"


def board_progress(board) -> tuple[int, int]:
    """Covered and flagged counts, used to tell whether a move changed anything."""
    covered = sum(1 for _, _, cell in board.iter_cells() if cell.is_covered)
    flagged = sum(1 for _, _, cell in board.iter_cells() if cell.is_flagged)
    return covered, flagged


def apply_move(game, sound_effects, mine_count, reveal_func, action, row, col) -> None:
    """Send one move through game logic and let the sound hook see it.

    The snapshot is only read by sound_effects.notify_move(); the game
    logic in between is unchanged from before the AI feature was added.
    """
    was_covered = game.board.get_cell(row, col).is_covered
    state_before = game.state

    game.process_move(action, (row, col), mine_count, reveal_func=reveal_func)

    cell_after = game.board.get_cell(row, col)
    sound_effects.notify_move(action, was_covered, cell_after, state_before, game.state)


def take_ai_turn(game, solver, sound_effects, mine_count, reveal_func) -> bool:
    """Play one AI move. Returns False when the AI could not make progress."""
    move = solver.make_move()
    if move is None:
        return False

    # The player can spend flags on the wrong cells, and FlagManager refuses to
    # place one once they run out. Without this the AI would keep asking for a
    # flag it cannot have and the game would stall.
    if move[0] == "flag" and flags_left(game, mine_count) <= 0:
        move = solver.random_move()
        if move is None:
            return False

    action, row, col = move
    render_message(f"AI ({solver.difficulty}) plays {action} on {cell_label(row, col)}.")

    before = board_progress(game.board)
    apply_move(game, sound_effects, mine_count, reveal_func, action, row, col)
    return board_progress(game.board) != before


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
    sound_effects = SoundEffects()

    # The solver reads the same Board the player plays on, so both sides see
    # the same mines, numbers, and flags.
    solver = AISolver(game.board, difficulty) if difficulty is not None else None

    # Game places mines itself on the first reveal. We still want the
    # cascade uncovering that RevealManager provides, so we pass its
    # reveal method as the reveal_func and flip its own first-reveal
    # flag so it doesn't try to place a second set of mines on top.
    reveal_manager = RevealManager(game.board, mine_count, game.mine_manager)

    def reveal_func(row: int, col: str) -> None:
        reveal_manager.first_reveal_done = True
        reveal_manager.reveal(row, col)

    # Tracks who made the last move, so the closing message names the right one.
    last_mover = "player"

    # Game loop, runs by getting how many flags are left, rendering the board, and getting the action from the user.
    while game.state == "PLAYING":
        render(game.board, flags_left(game, mine_count), STATUS_LABEL[game.state])

        if ai_mode == "auto":
            if not take_ai_turn(game, solver, sound_effects, mine_count, reveal_func):
                render_message("The AI has no move left to make.")
                break
            last_mover = "ai"
            time.sleep(AI_MOVE_DELAY)
            continue

        action, row, col = get_move()
        if action == "quit":
            render_message("Thanks for playing!")
            sound_effects.wait_until_done()
            return

        apply_move(game, sound_effects, mine_count, reveal_func, action, row, col)
        last_mover = "player"

        # Turns alternate: the AI answers every move the player completes.
        if ai_mode == "interactive" and game.state == "PLAYING":
            render(game.board, flags_left(game, mine_count), STATUS_LABEL[game.state])
            if take_ai_turn(game, solver, sound_effects, mine_count, reveal_func):
                last_mover = "ai"
            else:
                render_message("The AI has no move left to make.")

    # Final board + terminal status.
    render(game.board, flags_left(game, mine_count), STATUS_LABEL[game.state])
    if game.state == "VICTORY":
        if last_mover == "ai":
            render_message("The AI cleared the board! All safe cells uncovered.")
        else:
            render_message("You won! All safe cells cleared.")
    elif game.state == "LOSS":
        if last_mover == "ai":
            render_message("The AI hit a mine. Game over.")
        else:
            render_message("You hit a mine. Better luck next time!")
    # Let the win/mine clip finish before the process exits -- Sound.play()
    # is non-blocking, so without this the clip would get cut off here.
    sound_effects.wait_until_done()


# main loop
if __name__ == "__main__":
    main()
