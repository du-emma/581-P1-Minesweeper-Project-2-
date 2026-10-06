"""
Author: Megan Svoren
Date: 2026-10-05
Module: medium_ai.py
Outside Sources: GitHub Copilot Chat
Description: Medium AI for Minesweeper. Applies the "hidden neighbors equals
             adjacent mine count" rule to flag cells, the "flagged neighbors
             equals adjacent mine count" rule to reveal safe neighbors, and
             otherwise selects a random covered cell.
"""

import random

def find_move(board, uncovered_cells):
    """Apply a matching rule or return a random reveal move."""
    for row, col in uncovered_cells:
        cell = board.get_cell(row, col)
        neighbors = board.neighbors(row, col)

        hidden_neighbors = [
            (r, c) for r, c in neighbors
            if board.get_cell(r, c).is_covered and not board.get_cell(r, c).is_flagged
        ]
        flagged_neighbors = [
            (r, c) for r, c in neighbors
            if board.get_cell(r, c).is_flagged
        ]

        if len(hidden_neighbors) == cell.adjacent_mines:
            for r, c in hidden_neighbors:
                board.set_cell(r, c, is_flagged=True)
            return ("flag", *hidden_neighbors[0])

        if len(flagged_neighbors) == cell.adjacent_mines:
            reveal_neighbors = [
                (r, c) for r, c in hidden_neighbors
                if not board.get_cell(r, c).is_flagged
            ]
            for r, c in reveal_neighbors:
                board.set_cell(r, c, is_covered=False)
            return ("reveal", *reveal_neighbors[0]) if reveal_neighbors else None

    available_cells = [
        (r, c) for r, c in board.iter_positions()
        if board.get_cell(r, c).is_covered and not board.get_cell(r, c).is_flagged
    ]
    if not available_cells:
        return None

    row, col = random.choice(available_cells)
    return ("reveal", row, col)
