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
from display import render, render_message
from game import Game
from input_handler import get_mine_count, get_move
from reveal import RevealManager
from sound_effects import SoundEffects


# Map Game's internal state names to the user-facing status strings.
STATUS_LABEL = {
    "PLAYING": "Playing",
    "VICTORY": "Victory",
    "LOSS": "Game Over: Loss",
}


def main() -> None:
    print("Welcome to Minesweeper!")

    # edge case for when the user quits before entering the mine count.
    mine_count = get_mine_count()
    if mine_count is None:
        # Player hit Ctrl+C / Ctrl+D at the mine-count prompt.
        print("Goodbye!")
        return

    game = Game()
    sound_effects = SoundEffects()

    # Game places mines itself on the first reveal. We still want the
    # cascade uncovering that RevealManager provides, so we pass its
    # reveal method as the reveal_func and flip its own first-reveal
    # flag so it doesn't try to place a second set of mines on top.
    reveal_manager = RevealManager(game.board, mine_count, game.mine_manager)

    def reveal_func(row: int, col: str) -> None:
        reveal_manager.first_reveal_done = True
        reveal_manager.reveal(row, col)

    # Game loop, runs by getting how many flags are left, rendering the board, and getting the action from the user.
    while game.state == "PLAYING":
        flags_left = (
            game.flag_manager.get_flags_remaining()
            if game.flag_manager is not None
            else mine_count
        )
        render(game.board, flags_left, STATUS_LABEL[game.state])

        action, row, col = get_move()
        if action == "quit":
            render_message("Thanks for playing!")
            sound_effects.wait_until_done()
            return

        # Snapshot used only by sound_effects.notify_move(); game logic
        # below is unchanged from before this feature was added.
        was_covered = game.board.get_cell(row, col).is_covered
        state_before = game.state

        game.process_move(action, (row, col), mine_count, reveal_func=reveal_func)

        cell_after = game.board.get_cell(row, col)
        sound_effects.notify_move(action, was_covered, cell_after, state_before, game.state)

    # Final board + terminal status.
    flags_left = (
        game.flag_manager.get_flags_remaining()
        if game.flag_manager is not None
        else mine_count
    )
    render(game.board, flags_left, STATUS_LABEL[game.state])
    if game.state == "VICTORY":
        render_message("You won! All safe cells cleared.")
    else:
        render_message("You hit a mine. Better luck next time!")
    # Let the win/mine clip finish before the process exits -- Sound.play()
    # is non-blocking, so without this the clip would get cut off here.
    sound_effects.wait_until_done()


# main loop
if __name__ == "__main__":
    main()
