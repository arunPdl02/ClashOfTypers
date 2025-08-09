# Clash of Typers

A multiplayer typing game where players compete to break locks by typing strings within WPM targets.

## 🎮 Game Overview

- **Grid-based gameplay**: 5x5 grid of locks with different difficulties
- **Typing challenges**: Each lock requires typing a specific string within a WPM target
- **Real-time scoring**: Points awarded based on difficulty and WPM achieved
- **Time-based**: 1.5-minute game timer with synchronized start

## 🛜 Multiplayer Status

- ✅ Server-client implemented with raw TCP sockets and newline-delimited JSON
- ✅ Server enforces exclusive lock claiming and broadcasts updates
- ✅ Lobby with host-controlled start and countdown
- ✅ Works across machines (LAN/Internet) — server binds to `0.0.0.0`

## 🔧 Installation

```bash
# Clone the repository
git clone <repository-url>
cd ClashOfTypers

# Install dependencies
pip install pygame nltk

# Download NLTK data (once)
python -m nltk.downloader punkt gutenberg
```

## ▶️ Running (Multiplayer)

1) Start the server on the host machine:

```bash
python server.py
```

2) Start clients (same or different machines):

```bash
python client.py <UserName> <ServerIP> <Port>
# Examples
python client.py Alice 127.0.0.1 5555
python client.py Bob 192.168.1.50 5555
```

Notes:
- Ensure the server port `5555` is open on the host firewall/router.
- On the Internet, you may need to port-forward `5555` to the server machine.

## ⌨️ Controls

- Click a lock to claim
- Type the sentence; press Enter to submit
- ESC to cancel and release the claim
- H to toggle help overlay

## 🧠 Tech Overview

- `server.py`: Socket server with `select`, manages players, locks, and broadcasts
- `client.py`: Pygame UI client; connects via TCP; shows lobby, grid, typing screen
- `networking.py`: Client networking with background listener thread
- `messages.py`: Message type constants for the JSON protocol
- `game.py`: Grid/lock logic (claim, break, unclaim)
- `utils.py`: String generation (NLTK), timers
- `wpm.py`: WPM utilities

## 👥 Team

- Manan — Client UI and game logic
- Surya — Messaging protocol and networking
- Rushik — Configuration and utilities
- Arun — WPM calculation and server
