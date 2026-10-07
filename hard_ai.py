"""
Date: 2026-10-06
Module: hard_ai.py
Description: Hard AI for Minesweeper. Applies the Medium rules, then the
             1-2-1 pattern. Three side-by-side revealed cells that still need
             1, 2, 1 mines prove that the two outer hidden neighbors are mines
             and the inner hidden neighbor is safe, when those three cells are
             their whole frontier. Returns one move, or None when no rule
             applies so the AI controller (ai_solver.py) can make its random
             fallback move.
"""

from medium_ai import MediumAI
from medium_ai import find_move as find_medium_move


class HardAI:
    """Medium rules plus the 1-2-1 pattern.

    Positions are (row, col) with row 0-indexed and col a letter A-J, the same
    format Board uses. Rule methods return a move tuple for the AI controller
    to apply, or None when the rule does not apply. The board is not changed.
    """

    def __init__(self, board, uncovered_cells):
        self.board = board
        self.uncovered_cells = uncovered_cells
        self.medium = MediumAI(board, uncovered_cells)

    def apply_medium_rules(self):
        """return a Medium flag or reveal, or None"""
        return find_medium_move(self.board, self.uncovered_cells)

    def apply_121_rule(self):
        """flag one outer mine of a 1-2-1 pattern, or return None.

        One flag is enough for a single turn. On the next turn the Medium
        rules open the inner cell and flag the other outer mine.
        """
        move = self._scan_lines(horizontal=True)
        if move is not None:
            return move
        return self._scan_lines(horizontal=False)

    def _scan_lines(self, horizontal):
        """check every three consecutive cells in one orientation"""
        if horizontal:
            for row in range(self.board.rows):
                for col in range(self.board.cols - 2):
                    triple = [
                        (row, self.board.col_index_to_letter(col + offset))
                        for offset in range(3)
                    ]
                    move = self._match_triple(triple, ((-1, 0), (1, 0)))
                    if move is not None:
                        return move
            return None

        for col in range(self.board.cols):
            letter = self.board.col_index_to_letter(col)
            for row in range(self.board.rows - 2):
                triple = [(row + offset, letter) for offset in range(3)]
                move = self._match_triple(triple, ((0, -1), (0, 1)))
                if move is not None:
                    return move
        return None

    def _match_triple(self, triple, directions):
        """return a flag move when one side of this triple is a clean 1-2-1"""
        if not self._shows_121(triple):
            return None
        for d_row, d_col in directions:
            frontier = self._frontier(triple, d_row, d_col)
            if frontier is not None and self._frontier_is_exact(triple, frontier):
                outer_row, outer_col = frontier[0]
                return ("flag", outer_row, outer_col)
        return None

    def _shows_121(self, triple):
        """return True when the three revealed cells still need 1, 2, 1 mines.

        Flags already placed are subtracted, so a 2-3-2 sharing one flag
        reads as a 1-2-1 over the cells that are still hidden.
        """
        for (row, col), number in zip(triple, (1, 2, 1)):
            cell = self.board.get_cell(row, col)
            if cell.is_covered or cell.is_mine:
                return False
            remaining = cell.adjacent_mines - self.medium.count_flagged_neighbors(row, col)
            if remaining != number:
                return False
        return True

    def _frontier(self, triple, d_row, d_col):
        """return the three hidden cells beside the triple, or None.

        The cells sit one step in (d_row, d_col) from each number. All three
        must be on the board, covered, and unflagged.
        """
        frontier = []
        for row, col in triple:
            shifted = self._shift(row, col, d_row, d_col)
            if shifted is None:
                return None
            cell = self.board.get_cell(*shifted)
            if not cell.is_covered or cell.is_flagged:
                return None
            frontier.append(shifted)
        return frontier

    def _shift(self, row, col, d_row, d_col):
        """return the neighbor one step away, or None if it is off the board"""
        new_row = row + d_row
        new_col = self.board.col_letter_to_index(col) + d_col
        if not self.board.is_valid_position(new_row, new_col):
            return None
        return (new_row, self.board.col_index_to_letter(new_col))

    def _frontier_is_exact(self, triple, frontier):
        """return True when the frontier is the only hidden neighborhood.

        The left 1 touches the outer and inner cells, the right 1 touches the
        inner and its outer cell, and the middle 2 touches all three. Any
        extra hidden neighbor means a mine could sit somewhere else.
        """
        left, middle, right = triple
        outer_left, inner, outer_right = frontier
        hidden_left = set(self.medium.get_hidden_neighbors(*left))
        hidden_middle = set(self.medium.get_hidden_neighbors(*middle))
        hidden_right = set(self.medium.get_hidden_neighbors(*right))
        return (
            hidden_left == {outer_left, inner}
            and hidden_right == {inner, outer_right}
            and hidden_middle == {outer_left, inner, outer_right}
        )


def find_move(board, uncovered_cells):
    """apply Medium rules, then the 1-2-1 pattern.

    Returns ("flag", row, col) or ("reveal", row, col), or None if no rule
    applies. The board is left unchanged.
    """
    ai = HardAI(board, uncovered_cells)
    move = ai.apply_medium_rules()
    if move is not None:
        return move
    return ai.apply_121_rule()
