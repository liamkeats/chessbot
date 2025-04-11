# ChessBot

An automated chess-playing bot using Python, Selenium, and the Stockfish engine.

---

## 📦 Requirements

- **Python 3.7 or later**
- **Google Chrome browser**
- **ChromeDriver** (must match your Chrome version)
- **Stockfish engine**

---

## 🔧 Setup Instructions

### 1. Install Python Dependencies

In your terminal or command prompt, run:

```bash
pip install -r requirements.txt
```

This installs:
- `selenium` (controls the browser)
- `python-chess` (handles chess logic and Stockfish integration)
- `keyboard` (for triggering actions with hotkeys)

---

### 2. Download and Set Up Stockfish

1. Download the Stockfish engine from:  
   [https://stockfishchess.org/download/](https://stockfishchess.org/download/)
2. Extract the binary (`stockfish` or `stockfish.exe`) into the `chessbot/` folder.
3. Ensure your script references it like this:

```python
engine = chess.engine.SimpleEngine.popen_uci("stockfish")
```

---

### 3. Download and Set Up ChromeDriver

1. Find your Chrome version at:  
   `chrome://settings/help`
2. Download the matching version of ChromeDriver from:  
   [https://sites.google.com/chromium.org/driver/](https://sites.google.com/chromium.org/driver/)
3. Place `chromedriver.exe` inside the `chessbot/` folder.

---

### 4. Using the Chrome Profile Folder

The bot uses a custom Chrome user profile located at:

```
chessbot-chrome-profile/
```

This folder is **always kept empty in Git**, but will store your browser session when you run Chrome manually.

To launch Chrome with this profile:

```bash
chrome.exe --remote-debugging-port=9222 --user-data-dir="chessbot-chrome-profile"
```

This opens Chrome in a new window that your bot can connect to.

---

## ▶️ Running the Bot

Once everything is set up:

```bash
python scrapeboard.py
```

The bot will:
- Connect to the open Chrome window
- Detect the current game board (e.g., from Chess.com or Lichess)
- Use Stockfish to calculate the best move
- Output or optionally automate the move

---

## 🛠️ Notes

- The `chessbot-chrome-profile/` folder is included in the repo but stays empty (thanks to `.gitkeep`).
- Use Chrome with the launched user profile so your session and settings persist.
- Some sites may detect automation — use this bot responsibly.