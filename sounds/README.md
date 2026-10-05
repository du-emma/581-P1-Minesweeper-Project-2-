# Sound clips

Custom Project 2 feature (Arpa Das) — short, self-recorded `.wav` clips played
by `sound_effects.py`. Drop your recorded files in this folder using these
exact names:

| File          | Played when...                          |
|---------------|------------------------------------------|
| `uncover.wav` | a safe (non-mine) cell is revealed        |
| `flag.wav`    | a cell is flagged or unflagged            |
| `mine.wav`    | a mine is revealed (loss)                 |
| `win.wav`     | the board is fully cleared (victory)      |

If a file is missing, `SoundEffects` just skips playback for that event —
the game still runs fine without sound.
