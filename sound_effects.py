"""
Author: Arpa Das
Date: 2026-10-05
Module: sound_effects.py
Outside sources: pygame (third-party library, used only for pygame.mixer
    audio playback); Claude Code (Claude Sonnet 5) assisted drafting this
    module.
Description: Custom Project 2 feature. Plays short audio clips in response
    to gameplay events (uncovering a cell, flagging/unflagging a cell,
    hitting a mine, winning the game). This module only reacts to events the
    caller tells it about; it never reads the board or touches any
    Minesweeper game logic itself.
Inputs: SoundEffects() takes the directory holding the clip files and an
    enabled flag. notify_move() takes a before/after snapshot of a single
    move (action name, whether the target cell was covered before the move,
    the target Cell after the move, and the game state before/after).
Outputs: audio played through the default output device via pygame.mixer.
    No return values; nothing is written to the board or game state.
"""

import os
import time

try:
    import pygame
    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False

# Clip files the author records/produces herself. Dropped into SOUND_DIR
# with these exact names; see sounds/README.md for the full list.
UNCOVER_CLIP = "uncover.wav"
FLAG_CLIP = "flag.wav"
MINE_CLIP = "mine.wav"
WIN_CLIP = "win.wav"

DEFAULT_SOUND_DIR = os.path.join(os.path.dirname(__file__), "sounds")


class SoundEffects:
    """Loads and plays the four Project 2 sound-effect clips.

    Missing clip files or a missing/broken audio backend are not treated as
    errors: self.enabled drops to False and every play_* call becomes a
    silent no-op, so the game stays fully playable without sound.
    """

    def __init__(self, sound_dir: str = DEFAULT_SOUND_DIR, enabled: bool = True) -> None:
        self.sound_dir = sound_dir
        self.enabled = enabled and _PYGAME_AVAILABLE
        self._clips: dict[str, "pygame.mixer.Sound | None"] = {}

        if self.enabled:
            try:
                pygame.mixer.init()
            except pygame.error:
                # No audio device available (e.g. headless CI) -- disable
                # rather than crash the game.
                self.enabled = False

    def _load(self, filename: str):
        """Return the cached Sound for ``filename``, loading it on first use."""
        if filename in self._clips:
            return self._clips[filename]

        sound = None
        path = os.path.join(self.sound_dir, filename)
        if os.path.isfile(path):
            try:
                sound = pygame.mixer.Sound(path)
            except pygame.error:
                sound = None
        self._clips[filename] = sound
        return sound

    def _play(self, filename: str) -> None:
        if not self.enabled:
            return
        sound = self._load(filename)
        if sound is not None:
            sound.play()

    def play_uncover_sound(self) -> None:
        """Play when the player (or AI) safely uncovers a non-mine cell."""
        self._play(UNCOVER_CLIP)

    def play_flag_sound(self) -> None:
        """Play when a flag is placed or removed."""
        self._play(FLAG_CLIP)

    def play_mine_sound(self) -> None:
        """Play when a mine is uncovered (loss)."""
        self._play(MINE_CLIP)

    def play_win_sound(self) -> None:
        """Play when the board is fully cleared (victory)."""
        self._play(WIN_CLIP)

    def notify_move(
        self,
        action: str,
        was_covered: "bool | None",
        cell_after,
        state_before: str,
        state_after: str,
    ) -> None:
        """Pick the right clip (if any) for one completed move.

        Called once by the UI loop after Game.process_move() returns, with
        a snapshot taken right before and right after that call. Keeping the
        "which event -> which sound" decision in here means the UI loop
        only needs one extra line, and no Minesweeper game logic changes.

        :param action: the move's action string ('reveal', 'flag', 'unflag').
        :param was_covered: whether the target cell was covered before the
            move; None if there was no target cell (e.g. a quit).
        :param cell_after: the target cell after the move (same object the
            UI already reads to render the board), or None.
        :param state_before: game.state before the move ('PLAYING', ...).
        :param state_after: game.state after the move.
        """
        # A win takes priority over whatever the triggering move was.
        if state_before == "PLAYING" and state_after == "VICTORY":
            self.play_win_sound()
            return

        if action == "reveal" and was_covered and cell_after is not None and not cell_after.is_covered:
            if cell_after.is_mine:
                self.play_mine_sound()
            else:
                self.play_uncover_sound()
        elif action in ("flag", "unflag"):
            self.play_flag_sound()

    def wait_until_done(self, timeout: float = 3.0) -> None:
        """Block until the current clip finishes playing (or timeout).

        pygame.Sound.play() returns immediately, so a clip triggered on the
        game's final move (a win or a mine) would otherwise get cut off the
        instant the program exits right after. Call this once, right before
        the program ends.
        """
        if not self.enabled:
            return
        deadline = time.monotonic() + timeout
        while pygame.mixer.get_busy() and time.monotonic() < deadline:
            time.sleep(0.05)
