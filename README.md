# 581-P1-Minesweeper

# Running the program
Minesweeper uses the command line interface, and must be ran on a machine that has python downloaded.

Before running for the first time, install the dependencies (pygame, used for sound effects):
  py -m pip install -r requirements.txt

Use `py -m pip` rather than plain `pip` so pygame installs into the same Python that `py` runs. Without pygame the game still works, just with no sound.

Then run the game with the command:
  py index.py
  
The program will then ask you how many mines you would like to start with, and the game begins.

## Board System - Om Ghonasgi

The board is defined in `board.py` and provides the shared data model that every other module (mines, reveal, flags, display) reads from and writes to. It is intentionally state-only: no mine placement, no user input, no win/loss logic.

The module exports two classes and one constant:

- `Cell` - state for a single square.
- `Board` - the 10x10 grid of `Cell`s plus accessor methods.
- `COLUMN_LETTERS` - the string `"ABCDEFGHIJ"` used for column labels.

### Cell

Each `Cell` tracks the four state flags called out in the spec:

- `is_mine` - whether the cell hides a mine.
- `is_covered` - whether the cell is still hidden from the player.
- `is_flagged` - whether the player has flagged it.
- `adjacent_mines` - number of neighboring mines (0-8), set by mine-placement logic.

Every cell starts covered, unflagged, non-mine, with `adjacent_mines = 0`.

### Board

Create a fresh 10x10 board with no arguments:

```python
board = Board()
```

The board addresses cells using **0-indexed rows** (`0`-`9`, matching Python) and **letter columns** (`"A"`-`"J"`, matching the player-facing labels). If the UI receives input like `D5`, it should convert to:

```python
row = 4      # 5 - 1
col = "D"
board.get_cell(row, col)
```

Column letters are case-insensitive on input; `get_cell(0, "a")` and `get_cell(0, "A")` return the same cell.

### Methods

Position validation and column conversion:
- `is_valid_position(row, col_index)` - True if a 0-indexed `(row, col_index)` is on the board. `col_index` here is an integer, used internally after a letter has been converted.
- `col_letter_to_index(letter)` - Convert `"A"`-`"J"` to `0`-`9`. Raises `ValueError` on anything else.
- `col_index_to_letter(index)` - Convert `0`-`9` back to `"A"`-`"J"`.

Cell access:
- `get_cell(row, col)` - Return the `Cell` at `(row, col)`. Raises `ValueError` on a bad column letter, `IndexError` on a bad row.
- `set_cell(row, col, *, is_mine=None, is_covered=None, is_flagged=None, adjacent_mines=None)` - Update only the fields explicitly passed as keyword arguments; everything else is left untouched. This lets other modules change one attribute at a time without clobbering the rest.

Geometry:
- `neighbors(row, col)` - Return up to eight `(row, col_letter)` neighbor positions. Corners return 3, edges 5, interior cells 8.

Iteration helpers:
- `iter_positions()` - Yield every `(row, col_letter)` on the board (100 tuples).
- `iter_cells()` - Yield every `(row, col_letter, cell)` triple; the `cell` is the live reference, so mutations persist.

Development helper:
- `print_board()` - Print the whole board to stdout using single-character glyphs (`X` covered, `F` flagged, `O` uncovered-zero, `1`-`8` for adjacent-mine counts, `*` for an uncovered mine). Used for debugging; the real game uses `display.render` instead.


## Mine Placement - Adam Darst

The `mines.py` module defines the `MineManager` class, which manages mine placement and adjacent-mine calculations for the board.

### Main Responsibilities

- Places the requested number of mines randomly on the board.
- Protects the first clicked cell and its neighboring cells from containing mines.
- Clears existing mine placements before generating a new layout.
- Calculates the number of adjacent mines for every non-mine cell.
- Updates the shared `Board` object in place.

### Main Methods

- `place_mines(first_click, mine_count)` - Places between 10 and 20 mines while protecting the first-click area.
- `get_adjacent_cells(row, col)` - Returns the valid neighboring positions around a cell.
- `calculate_numbers()` - Computes and stores adjacent-mine counts for all non-mine cells.


## Flagging System - Arin Shah

Flagging is handled by the `FlagManager` class in `flags.py`.

Create it using the current board and the user-selected number of mines:

```python
flags = FlagManager(board, mine_count)
```

`mine_count` must be the same number used when placing mines. If the user chooses 15 mines, the player gets 15 flags.

### Functions
- `place_flag(row, col)` - Flags a covered cell and removes one available flag.
- `remove_flag(row, col)` - Unflags a cell and gives one flag back.
- `get_flags_remaining()` - Returns the number of flags still available.

The board uses **0-indexed rows** and **letter columns**. For example, user input `D5` must be converted to:

```python
row = 4
col = "D"
flags.place_flag(row, col)
```

The UI is responsible for converting user input like `D5`. The reveal system must check `cell.is_flagged` and not reveal the cell if it is `True`.



## Reveal System - Marcos Lepage

Uncovering is handled by the `RevealManager` class in `reveal.py`. It never prints; every call returns a `RevealResult` so `game.py` and `display.py` decide what the player sees.

Create it using the board, the user-selected number of mines, and the mine manager:

```python
reveal_manager = RevealManager(board, mine_count, mine_manager)
```

`mine_count` must be the same number used when placing mines and creating the `FlagManager`.

### Functions
- `reveal(row, col)` - Uncovers a cell and returns a `RevealResult`. Cascades automatically through blank cells.
- `reveal_all_mines()` - Uncovers every still-covered mine and returns their positions.

### RevealResult
- `outcome` - `SAFE`, `MINE`, `ALREADY_REVEALED`, `FLAGGED`, or `INVALID`.
- `revealed` - Every `(row, col)` uncovered by the call, in order.
- `adjacent_mines` - The requested cell's number, or `None` if nothing was uncovered or it was a mine.
- `hit_mine` - `True` only when a mine was uncovered.
- `reason` - Why a move was rejected, for the UI to show.

A cell with adjacent mines uncovers only itself. A blank cell uncovers its neighbors, and each blank neighbor cascades in turn, until the opening reaches numbered cells on every side. Flagged cells stay covered, so `get_flags_remaining()` stays accurate. A bad position returns `INVALID` instead of raising, so the UI can re-prompt.

`RevealManager` can also generate the minefield on the first reveal to guarantee a safe first click, but `game.py` does this itself and `index.py` sets `first_reveal_done = True`, so that path and `reveal_all_mines()` are unused in the assembled game.


## Game Logic - Jal Maru

The `game.py` module manages the overall game lifecycle, rule enforcement, and state transitions for Minesweeper. It acts as the central coordinator connecting the board data structure (`Board`), mine placement (`MineManager`), flagging mechanics (`FlagManager`), and uncovering logic (`reveal`).

### Key Responsibilities & Features

- **Game State Tracking**: Maintains and updates the internal state of the game (`PLAYING`, `VICTORY`, or `LOSS`).
- **First-Click Safety**: Ensures the player never hits a mine on their initial turn by triggering lazy mine generation via `MineManager` on the first reveal action.
- **Win & Loss Detection**:
  - **Win Condition**: Evaluates whether all non-mine cells on the board have been uncovered.
  - **Loss Condition**: Triggers game over when a mine cell is revealed.
- **Mine Uncovering on Defeat**: Automatically uncovers all hidden mines across the board when a loss occurs.
- **Component Coordination**: Directs user inputs/commands (`reveal`, `flag`, `unflag`) to their respective manager modules without directly handling terminal I/O or printing.

---

### Class Architecture

#### Attributes
- `board` (`Board`): The 10x10 grid instance.
- `mine_manager` (`MineManager`): Handles random mine generation and adjacent mine counts.
- `flag_manager` (`Optional[FlagManager]`): Handles flag placement limits and flag state updates.
- `state` (`str`): Current game status (`"PLAYING"`, `"VICTORY"`, or `"LOSS"`).
- `first_move` (`bool`): Flag tracking whether the next move is the initial click.

#### Primary Methods
- `process_move(command: str, target: Tuple[int, str], reveal_func=None) -> None`:  
  Processes user actions (`'reveal'`, `'flag'`, `'unflag'`), updates flag/mine managers, and evaluates post-move game state.
- `check_win() -> bool`:  
  Checks if all non-mine cells are uncovered. Returns `True` if victory conditions are met.
- `end_game(won: bool) -> None`:  
  Sets the state to `"VICTORY"` or `"LOSS"`. If `won=False`, executes `_reveal_all_mines()`.
- `_reveal_all_mines() -> None`:  
  Internal helper to set `is_covered = False` for all cells where `is_mine == True`.

  ## Terminal UI - Axel Bengoa

The terminal interface is split into two modules: `display.py` handles all output, and `input_handler.py` handles all input. Neither contains game rules. `display.py` only reads board state and never modifies it; `input_handler.py` only parses text and never decides whether a move is legal. Rules stay in `game.py`, `reveal.py`, and `flags.py`.

### Display

`display.py` renders the 10x10 grid with column letters A-J across the top and row numbers 1-10 down the side. Cells are drawn with single-character glyphs:

- `#` - covered.
- `F` - flagged.
- `1`-`8` - uncovered, showing the adjacent-mine count.
- ` ` (blank) - uncovered with zero adjacent mines.
- `*` - a mine, visible only after a loss uncovers them.

The glyphs are module-level constants, so changing the look of the board is a single edit. `display.py` replaces `board.print_board()`, which uses different glyphs and exists only for debugging.

### Display Functions
- `cell_glyph(cell)` - Return the glyph for a `Cell`. Takes the cell object, not a position.
- `render_board(board)` - Print the labeled grid.
- `render_status(mines_remaining, status)` - Print the remaining mine count and the game status.
- `render_menu()` - Print the numbered action menu.
- `render_message(message)` - Print one feedback line, prefixed with `>>`.
- `render(board, mines_remaining, status)` - Calls `render_board` and `render_status` together. This is what the game loop uses each turn.

### Input

`input_handler.py` prompts the player and re-prompts on anything invalid, so no malformed input reaches `game.py`.

### Input Functions
- `parse_cell(text)` - Convert `"D5"` into `(4, "D")`. Returns `None` if invalid. Accepts lowercase and spaces, so `"d5"` and `"d 5"` also work.
- `parse_action(text)` - Convert a menu selection into an action name. Accepts the number, the word, or the first letter. Returns `"reveal"`, `"flag"`, `"unflag"`, `"quit"`, or `None`.
- `get_mine_count()` - Prompt until the player enters a number from 10 to 20.
- `get_move()` - Prompt for an action and a cell. Returns `("reveal", 4, "D")` or `("quit", None, None)`.

Entering `b` at the cell prompt returns to the menu. `Ctrl+C` and `Ctrl+D` are caught and treated as quitting, so the game exits cleanly instead of crashing.

The board uses **0-indexed rows** and **letter columns** while the player types `D5`. `parse_cell` handles that conversion, so values from `get_move()` can be passed straight to `game.process_move()`:

```python
action, row, col = get_move()   # ("reveal", 4, "D")
game.process_move(action, (row, col), reveal_func=reveal)
```

