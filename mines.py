"""
Author: Adam Darst
Date: 2026-09-15
Module: mines.py
Outside sources: GPT-5.6 
Description: Module will place mines on the board and calculate adjacent mine counts for each non-mine cell.
    It will use the board class representing the game state and will modify it in place.
    The class will have to take in the first click position to avoid placing mines there and in adjacent cells.
"""

from random import Random
from board import Board

class MineManager:
    def __init__(self, board: Board, rng: Random | None = None) -> None:
        self.board = board
        self.rng = rng or Random()
        self.mine_count = 0

    def place_mines(self, first_click: tuple[int, str], mine_count: int) -> None:
        """Place the requested number of mines outside the protected area."""
        if not isinstance(mine_count, int) or not 10 <= mine_count <= 20:
            raise ValueError("mine_count must be an integer from 10 to 20")

        positions = list(self.board.iter_positions())
        self.mine_count = mine_count
        
        # Define the protected area: the first click and its adjacent cells
        protected_positions = {
            first_click,
            *self.get_adjacent_cells(*first_click),
        }
        
        # Filter out protected positions from the available positions
        available_positions = [
            position for position in positions if position not in protected_positions
        ]

        # Clear all cells before placing mines
        for row, col in positions:
            self.board.set_cell(row, col, is_mine=False)

        # Randomly select unique positions outside the protected area
        mine_positions = self.rng.sample(available_positions, self.mine_count)
        for row, col in mine_positions:
            self.board.set_cell(row, col, is_mine=True)

    def get_adjacent_cells(self, row: int, col: str) -> list[tuple[int, str]]:
        """Return valid neighboring positions around a cell."""
        return self.board.neighbors(row, col)

    def calculate_numbers(self) -> None:
        """Calculate adjacent mine counts for every non-mine cell."""
        for row, col, cell in self.board.iter_cells():
            # Skip mine cells as they do not need a count
            if cell.is_mine:
                continue
            
            # Calculate the number of adjacent mines
            adjacent_mines = sum(
                self.board.get_cell(neighbor_row, neighbor_col).is_mine
                for neighbor_row, neighbor_col in self.get_adjacent_cells(row, col)
            )
            self.board.set_cell(row, col, adjacent_mines=adjacent_mines)
    
