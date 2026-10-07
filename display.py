"""
Author: Axel Bengoa
Date: 2026-09-16
Module: display.py
Outside sources: Claude Code
Description: Terminal rendering for Minesweeper. Prints the 10x10 grid with
    column labels A-J and row numbers 1-10, the remaining mine count, the game
    status, the action menu, and feedback messages.
Inputs: None.
Outputs: it READS board state and never modifies it.

"""

from board import Board, Cell, COLUMN_LETTERS

# Symbols for each cell state . Changing them here updates the
# whole UI, so the Project 2 team only has one place to look.
COVERED = "#"
FLAGGED = "F"
MINE = "*"
EMPTY = " "  # uncovered cell with zero adjacent mines (spec: shown as empty)


def cell_glyph(cell: Cell) -> str:
    """Return the symbol used to draw a single cell."""
    # Covered cells hide everything except whether the player flagged them.
    if cell.is_covered:
        return FLAGGED if cell.is_flagged else COVERED
    # Uncovered cells: mines only show up once game logic uncovers them
    # (on a loss, game logic uncovers every mine so they all render here).
    if cell.is_mine:
        return MINE
    if cell.adjacent_mines == 0:
        return EMPTY
    return str(cell.adjacent_mines)


def render_board(board: Board) -> None:
    """Print the grid with A-J across the top and 1-10 down the side."""
    # Header: 3-char gutter so letters line up over the cell columns.
    print("   " + " ".join(COLUMN_LETTERS[: board.cols]))
    for r in range(board.rows):
        # board.py stores rows 0-indexed; players see 1-10, right-aligned
        # so "10" doesn't push its row out of line.
        row_label = f"{r + 1:>2} "
        glyphs = [
            cell_glyph(board.get_cell(r, COLUMN_LETTERS[c]))
            for c in range(board.cols)
        ]
        print(row_label + " ".join(glyphs))


def render_status(mines_remaining: int, status: str) -> None:
    """Print the remaining mine count and current game status."""
    print(f"\nMines remaining: {mines_remaining}")
    print(f"Status: {status}")


def render_menu() -> None:
    """Print the numbered list of actions the player can take ."""
    print("\nWhat would you like to do?")
    print("  1. Reveal")
    print("  2. Flag")
    print("  3. Unflag")
    print("  4. Quit")


def render_message(message: str) -> None:
    """Print a feedback message from game logic."""
    print(f"\n>> {message}")


def render(board: Board, mines_remaining: int, status: str) -> None:
    """Draw one full turn: blank line, board, then status."""
    print()
    render_board(board)
    render_status(mines_remaining, status)


# ----------------------------------------------------------------------
# Manual demo: `python display.py` shows every glyph without needing the
# mines/reveal/flag modules merged yet. Not used by the real game.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    demo = Board()
    demo.set_cell(1, "D", is_flagged=True)                        # flag
    demo.set_cell(2, "C", is_covered=False, adjacent_mines=1)     # numbers
    demo.set_cell(2, "D", is_covered=False, adjacent_mines=2)
    demo.set_cell(2, "E", is_covered=False, adjacent_mines=1)
    demo.set_cell(3, "D", is_covered=False, adjacent_mines=0)     # empty
    demo.set_cell(9, "J", is_covered=False, is_mine=True)         # mine
    render(demo, mines_remaining=9, status="Playing")
    render_menu()
