"""
Author: Marcos Lepage
Date: 2026-09-16
Module: reveal.py
Outside sources: Claude Opus 5 (Claude Code)
Description: Uncovering mechanics for Minesweeper. Uncovers a selected cell, detects
    a mine and reports the loss, reports the adjacent-mine number, and recursively
    cascades through blank cells. Mines are generated on the first reveal so the
    first click is always safe.
Inputs: the Board to uncover cells on, the MineManager used to build the minefield on
    the first reveal, the user-selected mine count (10-20), and a (row, col) position
    per request, where row is 0-indexed and col is a column letter A-J.
Outputs: a RevealResult for every request, plus in-place changes to the board's cell
    states. Nothing is printed; the UI and game-logic modules decide what to display.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from board import Board
from mines import MineManager


class RevealOutcome(Enum):
    """Why a call to ``RevealManager.reveal`` ended the way it did."""

    SAFE = "safe"                          # Cell uncovered, no mine
    MINE = "mine"                          # Cell hid a mine -> loss
    ALREADY_REVEALED = "already_revealed"  # Cell was already uncovered
    FLAGGED = "flagged"                    # Cell is flagged, refused
    INVALID = "invalid"                    # Position is off the board


@dataclass
class RevealResult:
    """The outcome of a single reveal request.

    Returned instead of printing so the caller can decide what to display:

        * ``outcome``        -- which ``RevealOutcome`` occurred
        * ``revealed``       -- every ``(row, col)`` uncovered by this call, in
                                the order they were uncovered; empty when
                                nothing changed
        * ``adjacent_mines`` -- adjacent-mine count of the *requested* cell, or
                                ``None`` when no cell was uncovered or the cell
                                was a mine
        * ``hit_mine``       -- convenience flag, True only on ``MINE``
        * ``reason``         -- short explanation for the UI to show on a
                                rejected move; ``None`` when the move succeeded
    """

    outcome: RevealOutcome
    revealed: list[tuple[int, str]] = field(default_factory=list)
    adjacent_mines: Optional[int] = None
    hit_mine: bool = False
    reason: Optional[str] = None

    @property
    def ok(self) -> bool:
        """Return True when the request actually uncovered at least one cell."""
        return self.outcome in (RevealOutcome.SAFE, RevealOutcome.MINE)

    @property
    def count(self) -> int:
        """Return how many cells this reveal uncovered."""
        return len(self.revealed)


class RevealManager:
    """Applies the uncovering rules to a ``Board``.

    Mines are not placed until the first reveal, and are then kept away from
    the clicked cell and its neighbors so that first click is always safe.

    ``mine_count`` is taken in the same position as ``FlagManager`` takes it,
    and must be the same value, so the flag counter matches the real mine
    total. ``place_mines`` rejects anything outside 10-20.
    """

    def __init__(
        self,
        board: Board,
        mine_count: int,
        mine_manager: MineManager,
    ) -> None:
        self.board = board
        self.mine_count = mine_count
        self.mine_manager = mine_manager
        self.first_reveal_done = False

    def reveal(self, row: int, col: str) -> RevealResult:
        """Uncover the cell at ``row`` (0-indexed) and ``col`` (letter A-J).

        Returns a ``RevealResult`` instead of raising, so the caller can treat a
        bad position as a move to retry rather than an error to handle.
        """
        position = self._normalize(row, col)
        if position is None:
            return RevealResult(
                outcome=RevealOutcome.INVALID,
                reason=f"Position out of bounds: ({row}, {col!r})",
            )
        row, col = position

        cell = self.board.get_cell(row, col)

        # A flagged cell is protected; the player must unflag it first.
        if cell.is_flagged:
            return RevealResult(
                outcome=RevealOutcome.FLAGGED,
                reason="That cell is flagged. Unflag it before revealing.",
            )

        # Re-revealing an open cell is a no-op, not a mistake.
        if not cell.is_covered:
            return RevealResult(
                outcome=RevealOutcome.ALREADY_REVEALED,
                adjacent_mines=cell.adjacent_mines,
                reason="That cell is already revealed.",
            )

        # Build the minefield around the first click so it lands safely. The
        # cell is re-read because placing mines rewrites the whole board.
        if not self.first_reveal_done:
            self.mine_manager.place_mines((row, col), self.mine_count)
            self.mine_manager.calculate_numbers()
            self.first_reveal_done = True
            cell = self.board.get_cell(row, col)

        # Uncovering a mine ends the game; only that one cell is opened.
        if cell.is_mine:
            self.board.set_cell(row, col, is_covered=False)
            return RevealResult(
                outcome=RevealOutcome.MINE,
                revealed=[(row, col)],
                adjacent_mines=None,
                hit_mine=True,
            )

        revealed: list[tuple[int, str]] = []
        self._reveal_recursive(row, col, revealed)
        return RevealResult(
            outcome=RevealOutcome.SAFE,
            revealed=revealed,
            adjacent_mines=cell.adjacent_mines,
        )

    def reveal_all_mines(self) -> list[tuple[int, str]]:
        """Uncover every still-covered mine and return their positions."""
        exposed: list[tuple[int, str]] = []
        for row, col, cell in self.board.iter_cells():
            if cell.is_mine and cell.is_covered:
                self.board.set_cell(row, col, is_covered=False)
                exposed.append((row, col))
        return exposed

    def _reveal_recursive(
        self, row: int, col: str, revealed: list[tuple[int, str]]
    ) -> None:
        """Uncover ``(row, col)``, cascading outward if it touches no mines.

        A blank cell has no number to show, so its neighbors are opened too, and
        each of those cascades in turn if it is also blank. Numbered cells are
        the boundary that stops the chain reaction.
        """
        cell = self.board.get_cell(row, col)

        # Already-open, flagged, and mine cells all end this branch.
        if not cell.is_covered or cell.is_flagged or cell.is_mine:
            return

        self.board.set_cell(row, col, is_covered=False)
        revealed.append((row, col))

        if cell.adjacent_mines != 0:
            return

        for neighbor_row, neighbor_col in self.board.neighbors(row, col):
            self._reveal_recursive(neighbor_row, neighbor_col, revealed)

    def _normalize(self, row: int, col: str) -> Optional[tuple[int, str]]:
        """Return ``(row, upper-case col)`` if on the board, otherwise None."""
        # Bools are ints in Python and would silently index the grid.
        if not isinstance(row, int) or isinstance(row, bool):
            return None
        try:
            col_index = self.board.col_letter_to_index(col)
        except ValueError:
            return None
        if not self.board.is_valid_position(row, col_index):
            return None
        return row, self.board.col_index_to_letter(col_index)
