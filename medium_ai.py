"""
Author: Megan Svoren, Jana Frady
Date: 2026-10-05, 2026-10-06
Module: medium_ai.py
Outside Sources: GitHub Copilot Chat, Claude AI
Description: Medium AI for Minesweeper. Applies the "hidden neighbors equals
             adjacent mine count" rule to flag cells and the "flagged neighbors
             equals adjacent mine count" rule to reveal safe neighbors. If
             neither rule applies, it returns None so the AI controller
             (ai_solver.py) can make its random fallback move.
"""

class MediumAI:
    """Rule-based helper for the Medium difficulty.

    Positions are (row, col) with row 0-indexed and col a letter A-J, the same
    format Board uses. Rule methods return a move tuple for the AI controller
    to apply, or None when the rule does not apply.
    """

    def __init__(self, board, uncovered_cells):
        self.board = board
        self.uncovered_cells = uncovered_cells

    # ------------------------------------------------------------------
    # Rule 1: flag cells that must be mines
    # ------------------------------------------------------------------

    def get_hidden_neighbors(self, row, col):
        """return neighbors that are covered and not flagged"""
        return [
            (r, c) for r, c in self.board.neighbors(row, col)
            if self.board.get_cell(r, c).is_covered
            and not self.board.get_cell(r, c).is_flagged
        ]

    def count_hidden_neighbors(self, row, col):
        """return how many neighbors are covered and not flagged"""
        return len(self.get_hidden_neighbors(row, col))

    def flag_certain_mines(self):
        """find a revealed number whose hidden neighbors must all be mines.

        A cell's hidden neighbors are all mines when
        (hidden neighbors + already-flagged neighbors) == its number.
        Returns ("flag", row, col) for one such neighbor, or None.
        """
        for row, col in self.uncovered_cells:
            cell = self.board.get_cell(row, col)
            if cell.is_mine or cell.adjacent_mines == 0:
                continue

            hidden = self.get_hidden_neighbors(row, col)
            if not hidden:
                continue

            flagged = self.count_flagged_neighbors(row, col)
            if len(hidden) + flagged == cell.adjacent_mines:
                r, c = hidden[0]
                return ("flag", r, c)
        return None

    def apply_mine_rule(self):
        """entry point for rule 1; returns a flag move or None"""
        return self.flag_certain_mines()

    # ------------------------------------------------------------------
    # Rule 2: reveal cells that must be safe
    # ------------------------------------------------------------------

    def count_flagged_neighbors(self, row, col):
        """return how many neighbors are flagged"""
        return sum(
            1 for r, c in self.board.neighbors(row, col)
            if self.board.get_cell(r, c).is_flagged
        )

    def get_safe_neighbors(self, row, col):
        """return covered, unflagged neighbors (safe once flags satisfy the number)"""
        return self.get_hidden_neighbors(row, col)

    def open_certain_safe_cells(self):
        """find a revealed number already satisfied by its flags; reveal the rest.

        Returns ("reveal", row, col) for one safe neighbor and leaves the board
        alone, so the controller applies the move (cascade, win/loss checks).
        The next call picks up the remaining safe neighbors.
        """
        for row, col in self.uncovered_cells:
            cell = self.board.get_cell(row, col)
            if cell.is_mine:
                continue
            if self.count_flagged_neighbors(row, col) == cell.adjacent_mines:
                safe = self.get_safe_neighbors(row, col)
                if safe:
                    r, c = safe[0]
                    return ("reveal", r, c)
        return None

    def apply_safe_rule(self):
        """entry point for rule 2; returns a reveal move or None"""
        return self.open_certain_safe_cells()

    # camelCase names to match the project's method list (same pattern as ai_solver.py)
    getHiddenNeighbors = get_hidden_neighbors
    countHiddenNeighbors = count_hidden_neighbors
    flagCertainMines = flag_certain_mines
    applyMineRule = apply_mine_rule
    countFlaggedNeighbors = count_flagged_neighbors
    getSafeNeighbors = get_safe_neighbors
    openCertainSafeCells = open_certain_safe_cells
    applySafeRule = apply_safe_rule


def find_move(board, uncovered_cells):
    """apply a matching rule and return its move, or None if no rule applies"""
    ai = MediumAI(board, uncovered_cells)

    move = ai.apply_mine_rule()
    if move is not None:
        return move

    return ai.apply_safe_rule()