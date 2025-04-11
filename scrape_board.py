import time
import logging
import tkinter as tk
import ctypes
import os
import threading
import keyboard
import chess
import chess.engine
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === TKINTER ===

# === CONFIGURATION ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKFISH_PATH = os.path.join(BASE_DIR, "stockfish", "stockfish-windows-x86-64-avx2.exe")
CHROME_PROFILE_PATH = os.path.join(BASE_DIR, "chessbot-chrome-profile")

# === INITIALIZE ENGINE ===
engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
analysis_depth = 5  # Default depth for Stockfish analysis
pause_main_loop = False

# === HOTKEY THREAD TO DYNAMICALLY ADJUST DEPTH ===
def listen_for_depth_change():
    global analysis_depth, pause_main_loop
    pause_main_loop = True
    try:
        print("\n🔧 Set new analysis depth: ", end="", flush=True)
        new_depth = input().strip()
        if new_depth.isdigit():
            analysis_depth = int(new_depth)
            print(f"✅ Analysis depth set to {analysis_depth}")
        else:
            print("❌ Invalid input. Please enter a number.")
    except Exception as e:
        print(f"❌ Error changing depth: {e}")
    finally:
        pause_main_loop = False
keyboard.add_hotkey("f8", listen_for_depth_change)

# === CHROME SETUP ===
options = webdriver.ChromeOptions()
options.add_argument("--log-level=3")
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument(f'--user-data-dir={CHROME_PROFILE_PATH}')
driver = webdriver.Chrome(options=options)

# === CHESS.COM LOAD ===
print("🔄 Launching chess.com...")
driver.get("https://www.chess.com/play")
WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, "board-layout-main")))
print("✅ Chess board loaded")

# === MODAL DISMISSAL ===
try:
    modal = driver.find_element(By.ID, "first-time-modal")
    driver.execute_script("arguments[0].remove();", modal)
    print("✅ Removed 'first-time-modal'")
except:
    print("⚠️ No modal found")

# === PIECE MAPS ===
piece_map = {
    'bp': '♙', 'br': '♖', 'bn': '♘', 'bb': '♗', 'bq': '♕', 'bk': '♔',
    'wp': '♟', 'wr': '♜', 'wn': '♞', 'wb': '♝', 'wq': '♛', 'wk': '♚',
}
piece_letter = {'p': '', 'r': 'R', 'n': 'N', 'b': 'B', 'q': 'Q', 'k': 'K'}
files = 'abcdefgh'

# === HELPERS ===
def to_square(x, y):
    return f"{files[x]}{y + 1}"

def game_started():
    try:
        driver.find_element(By.CSS_SELECTOR, ".clock-component .clock-time-monospace")
        return True
    except:
        return False

def get_board():
    while True:
        try:
            pieces = driver.find_elements(By.CSS_SELECTOR, ".piece")
            board = {}
            for piece in pieces:
                try:
                    classes = piece.get_attribute("class").split()
                    type_ = next((cls for cls in classes if cls in piece_map), None)
                    square = next((cls for cls in classes if cls.startswith("square-")), None)
                    if type_ and square:
                        coords = square.split("-")[1]
                        x, y = int(coords[0]) - 1, int(coords[1]) - 1
                        board[(x, y)] = type_
                except:
                    raise Exception("Stale element, will retry")
            return board
        except:
            print("🔄 Looks like you just started a new game or navigated away — retrying board read...")
            time.sleep(0.3)

def board_to_fen(board_dict):
    board = [[None for _ in range(8)] for _ in range(8)]
    for (x, y), piece in board_dict.items():
        symbol = piece[1].lower()
        board[y][x] = symbol.upper() if piece[0] == 'w' else symbol

    fen_rows = []
    for row in reversed(board):
        fen_row = ''
        empty = 0
        for square in row:
            if square is None:
                empty += 1
            else:
                if empty:
                    fen_row += str(empty)
                    empty = 0
                fen_row += square
        if empty:
            fen_row += str(empty)
        fen_rows.append(fen_row)

    fen = '/'.join(fen_rows) + ' w - - 0 1'
    return fen

def analyze_position(board_dict, last_moved_color):
    global engine, analysis_depth
    fen = board_to_fen(board_dict)
    board = chess.Board(fen)
    board.turn = chess.BLACK if last_moved_color == 'w' else chess.WHITE
    turn_str = "White" if board.turn == chess.WHITE else "Black"
    print(f"\n{turn_str} to move: with depth {analysis_depth}")
    try:
        result = engine.analyse(board, chess.engine.Limit(depth=analysis_depth))
        eval_score = result["score"].relative
        if eval_score.is_mate():
            eval_str = f"mate in {eval_score.mate()}"
        else:
            eval_str = f"{eval_score.score() / 100:.1f}"
        print(f"🔍 Stockfish recommends: {board.san(result['pv'][0])} (eval: {eval_str})")
    except Exception as e:
        print(f"❌ Stockfish analysis failed: {e}")
        print(f"🔎 Current FEN: {fen}")
        try:
            engine.quit()
        except:
            pass
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)

def detect_move(prev, curr):
    global engine
    removed = {k: v for k, v in prev.items() if k not in curr}
    added = {k: v for k, v in curr.items() if k not in prev}
    changed = {k: (prev[k], curr[k]) for k in prev if k in curr and prev[k] != curr[k]}
    last_moved_color = None
    move_found = False

    if len(added) == 1 and len(removed) == 1:
        to_pos, moved_piece = next(iter(added.items()))
        from_pos, _ = next(iter(removed.items()))
        symbol = piece_map[moved_piece]
        letter = piece_letter[moved_piece[1].lower()]
        is_capture = to_pos in prev
        last_moved_color = moved_piece[0]
        move_found = True
        prefix = (files[from_pos[0]] + 'x' if is_capture else to_square(*to_pos)) if letter == '' else (f"{letter}x{to_square(*to_pos)}" if is_capture else f"{letter}{to_square(*to_pos)}")
        color_str = "White" if moved_piece[0] == 'w' else "Black"
        if is_capture:
            taken_piece = prev[to_pos]
            print(f"⚔️ {symbol} {color_str} captured {piece_map[taken_piece]} at {to_square(*to_pos)} ({prefix})")
        else:
            print(f"{symbol} {color_str} played {prefix}")

    elif changed:
        for pos, (before, after) in changed.items():
            symbol = piece_map[after]
            letter = piece_letter[after[1].lower()]
            prefix = f"{files[pos[0]]}" if letter == '' else letter
            last_moved_color = after[0]
            move_found = True
            color_str = "White" if after[0] == 'w' else "Black"
            print(f"⚔️ {symbol} {color_str} captured {piece_map[before]} at {to_square(*pos)} ({prefix}x{to_square(*pos)})")

    if not move_found:
        print("⏸ No clear single move detected (maybe a castle or special move?)")

        # Determine last mover from current board if possible
        if prev != {} and list(prev.values())[0].startswith('w'):
            last_moved_color = 'w'
        else:
            last_moved_color = 'b'

        # Flip the turn: assume a move was made, even if it was a castle
        flipped_turn = 'b' if last_moved_color == 'w' else 'w'
        analyze_position(curr, flipped_turn)
    else:
        analyze_position(curr, last_moved_color)

# === MAIN LOOP ===
print("👀 Watching for moves...\nPress Ctrl+C to stop.")
previous = get_board()

try:
    while True:
        time.sleep(1)
        if pause_main_loop:
            continue

        if not game_started():
            print("⏳ Waiting for a game to start...")
            continue
        try:
            current = get_board()
        except:
            print("⚠️ Board read failed. Retrying...")
            continue
        if current != previous:
            detect_move(previous, current)
            previous = current
except KeyboardInterrupt:
    print("\n👋 Exiting. Thanks for playing!")
    driver.quit()   