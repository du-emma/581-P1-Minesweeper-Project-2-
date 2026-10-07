"""
Author: Om Ghonasgi
Date: 2026-09-14
Module: board.py
Outside sources: Cursor with Claude Opus 4.7 Agent, ChatGPT
Description: Board representation for Minesweeper. Meant to initalize a 10x10 board with cells. Implements various methods to access and modify the board.

Defines the ``Cell`` and ``Board`` classes that hold the state of a
Minesweeper game. It exists as a stable data model that other modules (mine placement,
input handling, game loop) build on top of. A ``print_board`` helper is
included so the board can be inspected during development.
"""

from typing import Iterator, Optional
# Column letters A..J for the 10-wide board.
COLUMN_LETTERS = "ABCDEFGHIJ"


class Cell:
    """A single cell on the Minesweeper board.

    A cell tracks the four state flags called out in the spec:

        * ``is_mine``     -- whether this cell hides a mine
        * ``is_covered``  -- whether the cell is still covered
        * ``is_flagged``  -- whether the player has flagged it
        * ``adjacent_mines`` -- number of neighboring mines (0-8)
    """

    def __init__(
        self,
        is_mine: bool = False,
        is_covered: bool = True,
        is_flagged: bool = False,
        adjacent_mines: int = 0,
    ) -> None:
        self.is_mine = is_mine
        self.is_covered = is_covered
        self.is_flagged = is_flagged
        self.adjacent_mines = adjacent_mines

    def __repr__(self) -> str:
        return (
            "Cell("
            f"is_mine={self.is_mine}, "
            f"is_covered={self.is_covered}, "
            f"is_flagged={self.is_flagged}, "
            f"adjacent_mines={self.adjacent_mines})"
        )


class Board:
    """A 10x10 Minesweeper board.

    Positions are stored 0-indexed internally. Helpers are provided to
    convert to and from the user-facing labels (columns ``A``-``J``,
    rows ``1``-``10``).
    """

    def __init__(self) -> None:
        self.rows = 10
        self.cols = 10
        self._grid: list[list[Cell]] = [
            [Cell() for _ in range(self.cols)] for _ in range(self.rows)
        ]

    # ------------------------------------------------------------------
    # Position validation and column-letter conversion
    # ------------------------------------------------------------------

    def is_valid_position(self, row: int, col: int) -> bool:
        """Return True if ``(row, col)`` is a valid 0-indexed position."""
        return 0 <= row < self.rows and 0 <= col < self.cols

    def col_letter_to_index(self, letter: str) -> int:
        """Convert a column letter (e.g. ``'A'``) to a 0-indexed column."""
        if not isinstance(letter, str) or len(letter) != 1:
            raise ValueError(
                f"Column letter must be a single character, got: {letter!r}"
            )
        idx = COLUMN_LETTERS.find(letter.upper())
        if idx == -1:
            raise ValueError(f"Invalid column letter: {letter!r}")
        return idx

    def col_index_to_letter(self, index: int) -> str:
        """Convert a 0-indexed column into its letter (e.g. ``'A'``)."""
        if not 0 <= index < len(COLUMN_LETTERS):
            raise ValueError(f"Column index out of range: {index}")
        return COLUMN_LETTERS[index]

    # ------------------------------------------------------------------
    # Cell accessors
    # ------------------------------------------------------------------

    def get_cell(self, row: int, col: str) -> Cell:
        """Return the ``Cell`` at ``row`` (0-indexed) and ``col`` (letter A-J)."""
        col_idx = self.col_letter_to_index(col)
        if not self.is_valid_position(row, col_idx):
            raise IndexError(f"Position out of bounds: ({row}, {col!r})")
        return self._grid[row][col_idx]

    def set_cell(
        self,
        row: int,
        col: str,
        *,
        is_mine: Optional[bool] = None,
        is_covered: Optional[bool] = None,
        is_flagged: Optional[bool] = None,
        adjacent_mines: Optional[int] = None,
    ) -> None:
        """Update one or more attributes of the cell at ``(row, col)``.

        ``row`` is a 0-indexed integer and ``col`` is a column letter
        (``'A'``..``'J'``). Only the keyword arguments explicitly provided
        are modified; the remaining cell state is left untouched. This
        keeps ``Board`` a pure state container -- the rules around *when*
        a cell should change state live in other modules.
        """
        cell = self.get_cell(row, col)
        if is_mine is not None:
            cell.is_mine = is_mine
        if is_covered is not None:
            cell.is_covered = is_covered
        if is_flagged is not None:
            cell.is_flagged = is_flagged
        if adjacent_mines is not None:
            cell.adjacent_mines = adjacent_mines

    def neighbors(self, row: int, col: str) -> list[tuple[int, str]]:
        """Return the (up to eight) neighbor positions of ``(row, col)``.

        ``row`` is 0-indexed and ``col`` is a column letter. The returned
        positions use the same format: ``(row_int, col_letter)``.
        """
        col_idx = self.col_letter_to_index(col)
        if not self.is_valid_position(row, col_idx):
            raise IndexError(f"Position out of bounds: ({row}, {col!r})")
        result: list[tuple[int, str]] = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col_idx + dc
                if self.is_valid_position(nr, nc):
                    result.append((nr, self.col_index_to_letter(nc)))
        return result

    # ------------------------------------------------------------------
    # Iteration helpers
    # ------------------------------------------------------------------

    def iter_positions(self) -> Iterator[tuple[int, str]]:
        """Yield every ``(row, col)`` position on the board.

        ``row`` is 0-indexed and ``col`` is a column letter.
        """
        for r in range(self.rows):
            for c in range(self.cols):
                yield r, self.col_index_to_letter(c)

    def iter_cells(self) -> Iterator[tuple[int, str, Cell]]:
        """Yield every ``(row, col, cell)`` triple on the board.

        ``row`` is 0-indexed and ``col`` is a column letter.
        """
        for r, col_letter in self.iter_positions():
            yield r, col_letter, self.get_cell(r, col_letter)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def print_board(self) -> None:
        """Print the whole board.

        Every covered cell is drawn as ``X`` (the initial state of every
        cell on a fresh board), flagged cells as ``F``, and uncovered
        cells as either their adjacent-mine count or a blank for zero.
        Mines that have been uncovered are drawn as ``*``.
        """
        # Header row: three leading spaces for the row-number gutter, then
        # each column letter separated by a space so it lines up with the
        # single-character cell glyphs below.
        print("   " + " ".join(COLUMN_LETTERS[: self.cols]))
        for r in range(self.rows):
            # Right-align the row number in a 2-char field so rows 1..10
            # stay aligned.
            row_label = f"{r + 1:>2} "
            glyphs = [
                self._glyph_for(self.get_cell(r, self.col_index_to_letter(c)))
                for c in range(self.cols)
            ]
            print(row_label + " ".join(glyphs))

    def _glyph_for(self, cell: Cell) -> str:
        """Return the single-character glyph used to render ``cell``."""
        if cell.is_covered:
            return "F" if cell.is_flagged else "X" # Flagged (F) or covered cell (X)
        if cell.is_mine:
            return "*" # Mine
        if cell.adjacent_mines == 0:
            return "O" # Empty cell
        if cell.adjacent_mines >= 1:
            return str(cell.adjacent_mines) # Number of adjacent mines