"""
Author: Jal Maru, Serom Kim
Date: 2026-10-06
Module: game.py
Description: Game logic controller for Minesweeper. Manages the inherited
    Project 1 game state and the Project 2 player/AI turn flow.
"""

from typing import Optional, Tuple

from ai_solver import AISolver
from board import Board
from flags import FlagManager
from mines import MineManager


class Game:
    """Manage Minesweeper state, moves, and player/AI turns."""
    def __init__(self) -> None:
        # Project 1 state
        self.board = Board()
        self.mine_manager = MineManager(self.board)
        self.flag_manager: Optional[FlagManager] = None
        self.state: str = "PLAYING"
        self.first_move: bool = True

        # Project 2 state
        self.mode: str = "off"
        self.difficulty: Optional[str] = None
        self.current_turn: str = "player"
        self.mine_count: int = 10
        self.ai_solver: Optional[AISolver] = None

    # ------------------------------------------------------------------
    # Project 2 game/turn integration
    # ------------------------------------------------------------------

    def startGame(
        self,
        mode: str = "off",
        difficulty: Optional[str] = None,
        mine_count: int = 10,
    ) -> None:
        """
        Configure a new game and create the AI solver when needed.
        mode:
            "off"         - player only
            "interactive" - player and AI alternate turns
            "auto"        - AI plays by itself
        difficulty:
            "easy"
            "medium"
            "hard"
        """
        mode = mode.strip().lower()
        if mode not in ("off", "interactive", "auto"):
            raise ValueError("Mode must be off, interactive, or auto.")
        if not isinstance(mine_count, int) or not 10 <= mine_count <= 20:
            raise ValueError("mine_count must be an integer from 10 to 20.")
        if mode == "off":
            difficulty = None
        else:
            if difficulty is None:
                raise ValueError("AI difficulty is required when AI mode is enabled.")
            difficulty = difficulty.strip().lower()
            if difficulty not in ("easy", "medium", "hard"):
                raise ValueError("Difficulty must be easy, medium, or hard.")
        self.mode = mode
        self.difficulty = difficulty
        self.mine_count = mine_count

        # In auto mode the AI begins immediately.
        # Otherwise the human player begins.
        if mode == "auto":
            self.current_turn = "ai"
        else:
            self.current_turn = "player"

        if difficulty is not None:
            self.ai_solver = AISolver(self.board, difficulty)
        else:
            self.ai_solver = None

    def playerTurn(
        self,
        command: str,
        target: Tuple[int, str],
        reveal_func=None,
    ) -> bool:
        """
        Apply one human player's move.

        Returns True if the move actually changed the board.
        In interactive mode, a successful move passes control to the AI.
        """
        # No moves are accepted after the game ends.
        if self.state != "PLAYING":
            return False
        
        # Do not allow the player to move during the AI's turn.
        if self.current_turn != "player":
            return False
        before = self._board_progress()
        self.process_move(
            command,
            target,
            self.mine_count,
            reveal_func=reveal_func,
        )
        after = self._board_progress()
        changed = before != after

        # Only switch turns after a valid move.
        if (
            changed
            and self.state == "PLAYING"
            and self.mode == "interactive"
        ):
            self.switchTurn()
        return changed

    def aiTurn(self, reveal_func=None):
        """
        Ask the selected AI for one move and apply it.
        Returns:
            ("reveal", row, col)
            ("flag", row, col)
            ("unflag", row, col)

        Returns None if the AI cannot make a move.
        """
        # AI cannot move after the game is over.
        if self.state != "PLAYING":
            return None

        # AI is only used in interactive or auto mode.
        if self.mode not in ("interactive", "auto"):
            return None

        # Make sure it is actually the AI's turn.
        if self.current_turn != "ai":
            return None
        if self.ai_solver is None:
            return None

        # Ask AISolver for a move.
        move = self.ai_solver.make_move()
        if move is None:
            return None
        action, row, col = move

        # A Medium/Hard rule may determine that a flag should be placed.
        # If there are no flags remaining, fall back to a random reveal.
        if action == "flag" and self._flags_remaining() <= 0:
            move = self.ai_solver.random_move()
            if move is None:
                return None
            action, row, col = move
        before = self._board_progress()

        # Apply the AI move through Game so all normal Minesweeper
        # rules and win/loss checks still happen in one place.
        self.process_move(
            action,
            (row, col),
            self.mine_count,
            reveal_func=reveal_func,
        )
        changed = self._board_progress() != before

        # If a rule somehow returned a move that could not be applied,
        # try the AI controller's random fallback once.
        if not changed and self.state == "PLAYING":
            fallback = self.ai_solver.random_move()
            if fallback is not None and fallback != move:
                action, row, col = fallback
                self.process_move(
                    action,
                    (row, col),
                    self.mine_count,
                    reveal_func=reveal_func,
                )
                move = fallback
                changed = self._board_progress() != before

        # Only switch turns if the game is still active.
        if self.state == "PLAYING":
            if self.mode == "interactive":
                self.switchTurn()
            elif self.mode == "auto":
                # AI keeps control in automatic mode.
                self.current_turn = "ai"
        if changed:
            return move
        return None

    def switchTurn(self) -> str:
        """
        Switch between player and AI in interactive mode.
        Returns the name of the new current turn.
        """
        if self.mode != "interactive":
            return self.current_turn
        if self.state != "PLAYING":
            return self.current_turn
        if self.current_turn == "player":
            self.current_turn = "ai"
        else:
            self.current_turn = "player"
        return self.current_turn

    def getStatus(self) -> dict:
        """
        Return information about the current game.
        """
        return {
            "state": self.state,
            "mode": self.mode,
            "difficulty": self.difficulty,
            "turn": self.current_turn,
        }

    def restartGame(self) -> None:
        """
        Reset the board while keeping the selected mode,
        difficulty, and mine count.
        """
        old_mode = self.mode
        old_difficulty = self.difficulty
        old_mine_count = self.mine_count

        # Recreate all Project 1 game objects.
        self.board = Board()
        self.mine_manager = MineManager(self.board)
        self.flag_manager = None
        self.state = "PLAYING"
        self.first_move = True
        # Restore the selected Project 2 settings.
        self.startGame(old_mode, old_difficulty, old_mine_count)
    
    # Existing Project 1 game logic
    def process_move(
        self,
        command: str,
        target: Tuple[int, str],
        mine_count: int,
        reveal_func=None,
    ) -> None:
        """
        Process a reveal, flag, or unflag command and evaluate
        the resulting game state.
        """
        # Once the game ends, no more moves are accepted.
        if self.state != "PLAYING":
            return
        row, col = target
        cell = self.board.get_cell(row, col)
        if command == "reveal":
            # Flagged cells cannot be uncovered.
            if cell.is_flagged:
                return
            # Revealing an already open cell does nothing.
            if not cell.is_covered:
                return
            # Safe first click:
            # mines are not generated until the first reveal.
            if self.first_move:
                self.mine_manager.place_mines((row, col), mine_count)

                self.mine_manager.calculate_numbers()
                self.flag_manager = FlagManager(self.board, mine_count)
                self.first_move = False
            # Use RevealManager's recursive reveal logic when supplied.
            if reveal_func:
                reveal_func(row, col)
            else:
                self.board.set_cell(row, col, is_covered=False)
            # Re-read the cell after mine placement/reveal.
            cell = self.board.get_cell(row, col)
            # Check for loss.
            if cell.is_mine:
                self.end_game(won=False)
            # Check for victory.
            elif self.check_win():
                self.end_game(won=True)
        elif command == "flag" and self.flag_manager:
            self.flag_manager.place_flag(row, col)
        elif command == "unflag" and self.flag_manager:
            self.flag_manager.remove_flag(row, col)

    def check_win(self) -> bool:
        """
        Return True if every non-mine cell has been uncovered.
        """
        for _, _, cell in self.board.iter_cells():
            if not cell.is_mine and cell.is_covered:
                return False
        return True

    def end_game(self, won: bool) -> None:
        """
        Update the game state after a victory or loss.
        """
        if won:
            self.state = "VICTORY"
        else:
            self.state = "LOSS"
            self._reveal_all_mines()

    def _reveal_all_mines(self) -> None:
        """
        Reveal every mine after a loss.
        """
        for row, col, cell in self.board.iter_cells():
            if cell.is_mine:
                self.board.set_cell(row, col, is_covered=False)

    # Internal helpers
    def _flags_remaining(self) -> int:
        """
        Return the number of flags still available.
        """
        # Before the first reveal, FlagManager has not been created yet.
        if self.flag_manager is None:
            return self.mine_count
        return self.flag_manager.get_flags_remaining()
    
    def _board_progress(self) -> tuple[int, int]:
        """
        Return covered and flagged counts.

        Used to determine whether a requested move actually changed
        the game board.
        """
        covered = sum(
            1
            for _, _, cell in self.board.iter_cells()
            if cell.is_covered
        )
        flagged = sum(
            1
            for _, _, cell in self.board.iter_cells()
            if cell.is_flagged
        )
        return covered, flagged