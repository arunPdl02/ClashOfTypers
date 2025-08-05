# Clash of Typers

A multiplayer typing game where players compete to break locks by typing strings within WPM targets.

## 🎮 Game Overview

- **Grid-based gameplay**: 5x5 grid of locks with different difficulties
- **Typing challenges**: Each lock requires typing a specific string within a WPM target
- **Real-time scoring**: Points awarded based on difficulty and WPM achieved
- **Time-based**: 5-minute game timer with countdown

## 🚀 Recent Improvements (Latest Update)

### ✅ **Fixed Input System**
- **Problem**: Key holding caused multiple character input
- **Solution**: Implemented key state tracking to prevent repeated characters
- **Result**: Clean, responsive typing experience

### ✅ **Enhanced Scoreboard**
- **Added**: Progress bar showing lock completion
- **Added**: Detailed statistics display
- **Added**: Real-time WPM tracking during typing
- **Added**: Better visual layout with additional stats bar

### ✅ **Real WPM Calculation**
- **Implemented**: `WPMCalculator` class for accurate typing speed measurement
- **Features**: Tracks keystrokes, calculates actual WPM, handles timing
- **Integration**: Seamlessly integrated with typing challenges

## 🎯 Game Features

### **Lock System**
- **Easy**: 15-30 WPM target, 1-5 word strings
- **Medium**: 30-50 WPM target, 5-10 word strings  
- **Hard**: 50-70 WPM target, 10-15 word strings

### **Scoring System**
- Points calculated based on string length and WPM achieved
- Higher difficulty = higher potential points
- Real-time score tracking

### **Visual Design**
- Color-coded locks by difficulty (Green=Easy, Orange=Medium, Purple=Hard)
- Fade-in score display on game start
- Progress bar for lock completion
- Detailed HUD with all game statistics

## 🛠️ Technical Implementation

### **Core Components**
- `client.py`: Main game client with Pygame UI
- `game.py`: Game logic and lock management
- `wpm.py`: WPM calculation and typing tracking
- `utils.py`: Helper functions and string generation
- `config.py`: Game constants and configuration
- `networking.py`: Network communication framework
- `messages.py`: Message protocol definitions

### **Input Handling**
```python
# Improved key state tracking
key_states = {}  # Prevents key holding issues
handle_typing_input(event, user_string, wpm_calculator)
```

### **WPM Calculation**
```python
wpm_calculator = WPMCalculator()
wpm_calculator.start_typing()
wpm_calculator.record_keystroke(char)
wpm = wpm_calculator.finish_typing()
```

## 🎮 How to Play

1. **Start the game**: Run `python client.py`
2. **Click on locks**: Select any available lock to attempt
3. **Type the challenge**: Type the displayed string within the time limit
4. **Achieve WPM target**: Meet or exceed the required WPM to break the lock
5. **Score points**: Earn points based on difficulty and performance
6. **Complete all locks**: Try to break all locks before time runs out

## 🔧 Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd ClashOfTypers

# Install dependencies
pip install pygame nltk

# Run the game
python client.py
```

## 📊 Current Status

- ✅ **Single-player gameplay**: Fully functional
- ✅ **Input system**: Fixed key holding issues
- ✅ **Scoreboard**: Enhanced with detailed statistics
- ✅ **WPM calculation**: Real-time typing speed tracking
- ✅ **Visual improvements**: Progress bars and better UI
- 🚧 **Multiplayer**: Network framework ready, server implementation needed
- 🚧 **Server**: Basic structure, needs full implementation

## 🎯 Next Steps

1. **Server Implementation**: Complete multiplayer functionality
2. **Network Integration**: Enable client-server communication
3. **Player Management**: Add player names and icons
4. **Real-time Features**: Live player cursors and updates
5. **Testing**: Comprehensive testing and bug fixes

## 👥 Team

- **Manan**: Client UI and game logic
- **Surya**: Messaging protocol and networking
- **Rushik**: Configuration and utilities
- **Arun**: WPM calculation and server framework

---

**Latest Update**: Fixed input system and enhanced scoreboard with real WPM tracking! 🎉
