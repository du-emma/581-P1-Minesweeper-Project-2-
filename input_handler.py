"""
Author: Axel Bengoa
Date: 2026-09-16
Module: input_handler.py
Outside sources: Claude Code
Description: Reads and validates everything the player types. Re-prompts on
    invalid input instead of crashing, then hands clean values to game logic.

This module only parses input.
"""

from typing import Optional

from board import COLUMN_LETTERS
from display import render_ai_menu, render_difficulty_menu, render_menu

MIN_MINES = 10
MAX_MINES = 20
NUM_ROWS = 10

# Menu numbers and typed words both map to the same action (original).
ACTION_ALIASES = {
    "1": "reveal", "reveal": "reveal", "r": "reveal",
    "2": "flag", "flag": "flag", "f": "flag",
    "3": "unflag", "unflag": "unflag", "u": "unflag",
    "4": "quit", "quit": "quit", "q": "quit", "exit": "quit",
}

BACK_WORDS = {"b", "back"}

# How the AI takes part, and how much reasoning it uses.
AI_MODE_ALIASES = {
    "1": "off", "off": "off", "o": "off", "none": "off",
    "2": "interactive", "interactive": "interactive", "i": "interactive",
    "3": "auto", "auto": "auto", "a": "auto",
}

AI_DIFFICULTY_ALIASES = {
    "1": "easy", "easy": "easy", "e": "easy",
    "2": "medium", "medium": "medium", "m": "medium",
    "3": "hard", "hard": "hard", "h": "hard",
}


def _read(prompt: str) -> Optional[str]:
    """Wrapper around input() that returns None on Ctrl+C / Ctrl+D.

    Without this, those keys raise exceptions and crash the game, which
    counts against stress testing.
    """
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def parse_cell(text: str) -> Optional[tuple[int, str]]:
    """Turn "D5" into (4, "D"); return None for anything invalid."""
    cleaned = text.strip().upper().replace(" ", "")
    if len(cleaned) < 2:
        return None
    letter, number = cleaned[0], cleaned[1:]
    if letter not in COLUMN_LETTERS:
        return None
    # isdigit() rejects "-1", "5.0", "5a", etc. before int() can throw.
    if not number.isdigit():
        return None
    row = int(number)
    if not 1 <= row <= NUM_ROWS:
        return None
    # Players count rows from 1; board.py counts from 0.
    return row - 1, letter


def parse_action(text: str) -> Optional[str]:
    """Map menu input to an action name, or None if unrecognized."""
    return ACTION_ALIASES.get(text.strip().lower())


def parse_ai_mode(text: str) -> Optional[str]:
    """Map menu input to "off", "interactive", or "auto"."""
    return AI_MODE_ALIASES.get(text.strip().lower())


def parse_difficulty(text: str) -> Optional[str]:
    """Map menu input to "easy", "medium", or "hard"."""
    return AI_DIFFICULTY_ALIASES.get(text.strip().lower())


def get_mine_count() -> Optional[int]:
    """Prompt until the player picks a mine count from 10 to 20."""
    while True:
        raw = _read(f"How many mines? ({MIN_MINES}-{MAX_MINES}): ")
        if raw is None:
            return None
        raw = raw.strip()
        if raw.isdigit() and MIN_MINES <= int(raw) <= MAX_MINES:
            return int(raw)
        print(f"Please enter a whole number from {MIN_MINES} to {MAX_MINES}.")


def _choose(render_options, parser) -> Optional[str]:
    """Show a three-option menu and prompt until one of them is chosen.

    Returns None on Ctrl+C / Ctrl+D so the caller can exit cleanly.
    """
    render_options()
    while True:
        raw = _read("Choose 1-3: ")
        if raw is None:
            return None
        choice = parser(raw)
        if choice:
            return choice
        print("Invalid choice. Enter 1, 2, or 3.")


def get_ai_mode() -> Optional[str]:
    """Prompt until the player picks how the AI takes part."""
    return _choose(render_ai_menu, parse_ai_mode)


def get_ai_difficulty() -> Optional[str]:
    """Prompt until the player picks how much the AI reasons."""
    return _choose(render_difficulty_menu, parse_difficulty)


def _get_action() -> str:
    """Show the menu and prompt until a valid action is chosen."""
    render_menu()
    while True:
        raw = _read("Choose 1-4: ")
        if raw is None:
            return "quit"
        action = parse_action(raw)
        if action:
            return action
        print("Invalid choice. Enter 1, 2, 3, or 4.")


def _get_cell(action: str) -> Optional[tuple[int, str]]:
    """Prompt for a cell; None means the player backed out."""
    while True:
        raw = _read(f"Cell to {action} (e.g. D5), or 'b' to go back: ")
        if raw is None or raw.strip().lower() in BACK_WORDS:
            return None
        cell = parse_cell(raw)
        if cell:
            return cell
        print("Invalid cell. Use a column A-J followed by a row 1-10, like D5.")


def get_move() -> tuple[str, Optional[int], Optional[str]]:
    """Get one complete move from the player.

    Loops so that backing out of the cell prompt returns to the menu
    rather than submitting a half-finished move.
    """
    while True:
        action = _get_action()
        if action == "quit":
            return "quit", None, None
        cell = _get_cell(action)
        if cell is not None:
            row, col = cell
            return action, row, col


# ----------------------------------------------------------------------
# Manual demo: `python input_handler.py` lets you try the prompts and see
# exactly what game logic will receive. Not used by the real game.
# ----------------------------------------------------------------------
if __name__ == "__main__":
    count = get_mine_count()
    print(f"get_mine_count() -> {count}")
    if count is not None:
        while True:
            move = get_move()
            print(f"get_move() -> {move}")
            if move[0] == "quit":
                break
