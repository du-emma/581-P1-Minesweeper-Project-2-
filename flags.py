"""
Author: Arin Shah
Date: 2026-09-15
Module: flags.py
Outside sources: ChatGPT
Description:
Handles placing and removing flags on covered Minesweeper cells
and keeps track of the number of flags remaining.
"""


class FlagManager:

    def __init__(self, board, mine_count):
        self.board = board
        self.flags = mine_count

    def place_flag(self, row, col):
        """Place a flag if the cell is covered and flags are available."""

        cell = self.board.get_cell(row, col)

        if not cell.is_covered or cell.is_flagged or self.flags <= 0:
            return False

        cell.is_flagged = True
        self.flags -= 1
        return True

    def remove_flag(self, row, col):
        """Remove a flag from a flagged cell."""

        cell = self.board.get_cell(row, col)

        if not cell.is_flagged:
            return False

        cell.is_flagged = False
        self.flags += 1
        return True

    def get_flags_remaining(self):
        """Return the number of flags still available."""
        return self.flags