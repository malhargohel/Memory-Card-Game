# 🧠 Memory Card Game

A fun and interactive memory card matching game built with Python Flask and vanilla JavaScript. Test your memory skills, complete daily challenges, unlock achievements, and use powerful abilities to become a true memory master!

![Game Photo](image.png)
![Game Photo](Achievements.png)
![Game Photo](Stats_Page.png)
![Game Photo](Log_In_Page.png)
![Game Photo](Register_Page.png)

## 🚀 Live Demo

[Play the game here!](https://memory-card-game-mwdu.onrender.com)

## 🎮 Features

### Gameplay & Content
-   **Three Difficulty Levels**: Easy (6 pairs), Medium (8 pairs), and Hard (12 pairs).
-   **Four Card Themes**: Choose between Animals, Flags, Numbers, and Food.
-   **Daily Challenges**: A unique, seeded puzzle for all players to compete on every day.
-   **Earnable Power-Ups**: Make 2 matches in a row to earn a random power-up!
    -   **👀 Peek**: Briefly reveals 4 random cards.
    -   **⏱️ Time Freeze**: Pauses the timer for 5 seconds.
-   **Achievements & Badges**: Unlock achievements for completing milestones like winning with every theme or finishing a game with perfect moves.

### User System & Stats
-   **User Registration & Login**: Securely create and access your personal account.
-   **Game Statistics**: Track your progress, including games played, win rate, best time, and average moves per game.

### Design & UX
-   **Fully Responsive**: Works seamlessly on mobile & desktop.
-   **Sound Effects**: Audio feedback for flipping cards, making matches, and winning the game.
-   **Customizable Card Backs**: Choose from multiple patterns for the back of the cards.
-   **Modern UI**: Clean layout with gradient backgrounds and smooth animations.
-   **Notifications**: Get notified when you earn a power-up or unlock an achievement.

## 🛠️ Technologies Used

-   **Backend**: Python 3.x, Flask
-   **Database**: SQLite
-   **Frontend**: HTML5, CSS3, JavaScript (ES6+)
-   **Authentication**: Secure password hashing and session management
-   **Deployment**: Render

## 📋 Prerequisites

-   Python 3.7 or higher
-   pip (Python package manager)

## 🔧 Installation & Setup

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/malhargohel/memory-card-game.git](https://github.com/malhargohel/memory-card-game.git)
    cd memory-card-game
    ```

2.  **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Initialize the database**
    Run the Flask app for the first time. The `init_db()` function will automatically create the `memory_game.db` file and all necessary tables.
    ```bash
    python app.py
    ```

4.  **Run the application**
    ```bash
    python app.py
    ```

5.  **Open your browser**
    Navigate to `http://127.0.0.1:5000`

## 📁 Project Structure


memory-card-game/
│
├── app.py                # Flask backend with all game logic
├── memory_game.db        # SQLite database file
├── requirements.txt      # Python dependencies
├── README.md             # Project documentation
│
├── static/
│   ├── script.js         # Frontend game logic and interaction
│   └── sounds/           # Sound effect files (flip, match, win)
│
└── templates/
├── index.html        # Main game interface
├── login.html        # User login page
├── register.html     # User registration page
├── stats.html        # User statistics page
└── achievements.html # Achievements display page


## 🎯 How to Play

1.  **Create an account** or **log in** to track your progress.
2.  Choose your **Difficulty**, **Theme**, and **Card Back**.
3.  Click **"New Game"** to start a standard game or **"Daily Challenge"** for the day's special puzzle.
4.  Click on cards to flip them over and find matching pairs.
5.  Make **2 matches in a row** to earn a random power-up! Click the power-up button in the tray to use it.
6.  Match all pairs to win the game and see your final time and move count!
7.  Visit the **Achievements** page to see what you've unlocked.

## 🚀 Planned Features

-   **Leaderboards**: See how you rank against others in daily challenges and best times.
-   **Multiplayer Mode**: Challenge a friend in a head-to-head match.
-   **More Themes & Power-ups**: Continuously adding new content to keep the game fresh.

## 🔐 Security Features

-   **Password Hashing**: Secure bcrypt password storage.
-   **Session Management**: Flask's secure session handling.
-   **Input Validation**: Server-side validation for API endpoints.

## 👤 Author

**Malhar Gohel**
-   GitHub: [@malhargohel](https://github.com/malhargohel)

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
