"""
Author: Ellie Thach
Date: 2026-10-04
Module: easy_ai.py
Outside Sources: Claude
Description: Easy AI for Minesweeper. Picks one cell completely at random from the cells it is
             allowed to uncover. No reasoning used.
"""

import random

def find_move(available):
    """pick a random cell from available cells and return a reveal move"""
    if len(available) == 0:
        return None
    
    row, col = random.choice(available)
    return ("reveal", row, col)