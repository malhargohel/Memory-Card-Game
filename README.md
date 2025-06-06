# 🧠 Memory Card Game

A fun and interactive memory card matching game built with Python Flask and vanilla JavaScript. Test your memory skills by finding matching pairs of emoji cards!

![image](https://github.com/user-attachments/assets/6ed66e57-c305-4132-baed-0b93d1779559)


## 🎮 Features

- **Three Difficulty Levels**
  - Easy: 6 pairs (4×3 grid)
  - Medium: 8 pairs (4×4 grid) 
  - Hard: 12 pairs (6×4 grid)

- **Game Mechanics**
  - Move counter to track your performance
  - Real-time pair matching detection
  - Smooth card flip animations
  - Win celebration with final score

- **Design**
  - Fully responsive design (works on mobile & desktop)
  - Modern gradient background and card styling
  - Intuitive user interface
  - Accessible color schemes

## 🚀 Live Demo

[Play the game here!] https://web-production-f853.up.railway.app/

## 🛠️ Technologies Used

- **Backend**: Python 3.x, Flask
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Deployment**: Railway
- **Styling**: Custom CSS with Flexbox and Grid

## 📋 Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

## 🔧 Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/malhargohel/memory-card-game.git
   cd memory-card-game
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python app.py
   ```

4. **Open your browser**
   Navigate to `http://127.0.0.1:5000`

## 📁 Project Structure

```
memory-card-game/
│
├── app.py                 # Flask backend with game logic
├── requirements.txt       # Python dependencies
├── Procfile              # Deployment configuration
├── README.md             # Project documentation
│
├── static/
│   ├── style.css         # Game styling and animations
│   └── script.js         # Frontend game logic
│
└── templates/
    └── index.html        # Main game interface
```

## 🎯 How to Play

1. **Choose your difficulty** from the dropdown menu
2. **Click "New Game"** to start
3. **Click on cards** to flip them over
4. **Find matching pairs** by remembering card positions
5. **Match all pairs** to win the game!
6. **Try to complete** the game in as few moves as possible


## 🎨 Customization

### Adding New Card Symbols
Edit the `CARD_SYMBOLS` list in `app.py`:
```python
CARD_SYMBOLS = ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼']
# Add more emojis here!
```

### Changing Colors & Themes
Modify the CSS variables in `static/style.css`:
```css
/* Change the main gradient background */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Modify card colors */
.card.flipped {
    background: #667eea; /* Change this color */
}
```

### Adding Difficulty Levels
1. Add new options in `templates/index.html`
2. Update the difficulty logic in `app.py`
3. Add corresponding CSS grid classes in `static/style.css`

## 📊 Game Statistics

The game tracks:
- **Moves**: Number of card flip attempts
- **Pairs Found**: Current progress toward completion
- **Completion Time**: Time taken to finish (you can add this feature!)

## 🔧 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve the main game page |
| `/api/new-game` | POST | Start a new game session |
| `/api/flip-card` | POST | Flip a card and check for matches |
| `/api/game-state/<id>` | GET | Get current game state |

## 🐛 Known Issues & Future Improvements

### Current Limitations
- Game state is stored in memory (resets on server restart)
- No user accounts or persistent high scores
- No timer functionality

### Planned Features
- [ ] Add timer to track completion speed
- [ ] Implement high score leaderboard
- [ ] Add sound effects for card flips and matches
- [ ] Create user accounts and statistics
- [ ] Add multiplayer functionality
- [ ] Implement different card themes (animals, flags, numbers)

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some amazing feature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Areas for Contribution
- Add new card themes and symbols
- Implement sound effects
- Create additional difficulty levels
- Add accessibility improvements
- Write unit tests for game logic
- Improve mobile responsiveness

## 👤 Author

**Your Name**
- GitHub: [@malhargohel](https://github.com/malhargohel)
