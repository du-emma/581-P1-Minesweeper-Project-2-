"""
Author: Ellie Thach
Date: 2026-10-04
Module: ai_solver.py
Outside Sources: Claude
Description: Main AI controller for Minesweeper. The AISolver class is used for all three difficulty levels.
             It finds the cells that the AI can act on, which are covered and unflagged, sends the turn to the
             solver for the selected difficulty, and falls back to a random move when Medium/Hard rules have nothing
             to do. Also, it can find all the uncovered cells.
"""

from . import easy_ai

class AISolver:
    """chooses the AI's next move based on selected difficulty"""
    def __init__(self, board, difficulty = "easy"):
        difficulty = difficulty.strip().lower()
        if difficulty not in ("easy", "medium", "hard"):
            raise ValueError("Difficulty must be easy, medium, or hard.")
        self.board = board
        self.difficulty = difficulty
    
    def get_available_cells(self):
        """return every (row, col) that is covered and unflagged"""
        available = []
        for row, col, cell in self.board.iter_cells():
            if cell.is_covered and not cell.is_flagged:
                available.append((row, col))
        return available

    def get_uncovered_cells(self):
        """return every (row, col) that is uncovered"""
        uncovered = []
        for row, col, cell in self.board.iter_cells():
            if not cell.is_covered:
                uncovered.append((row, col))
        return uncovered
    
    def make_move(self):
        """return AI's next move for current difficulty"""
        if self.difficulty != "easy":
            move = self.rule_based_move()
            if move is not None:
                return move
        return self.random_move() # easy mode always lands here, medium/hard lands here if no rules applied
    
    def random_move(self):
        """random reveal (easy ai mode, fallback for medium/hard mode)"""
        return easy_ai.find_move(self.get_available_cells())
    
    def rule_based_move(self):
        """asks medium/hard module for a move"""
        try:
            if self.difficulty == "hard":
                from .hard_ai import find_move
            else:
                from .medium_ai import find_move
        except ModuleNotFoundError:
            return None
        return find_move(self.board, self.get_uncovered_cells())
    
    getAvailableCells = get_available_cells
    getUncoveredCells = get_uncovered_cells
    makeMove = make_move
    randomMove = random_move