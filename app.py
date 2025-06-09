from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
import random
import time
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-for-production')

# --- CONFIGURATIONS ---
CARD_THEMES = {
    'animals': ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐸', '🐵', '🐯', '🐨', '🐷', '🐮', '🦄'],
    'flags': ['🇺🇸', '🇬🇧', '🇫🇷', '🇩🇪', '🇯🇵', '🇨🇦', '🇦🇺', '🇧🇷', '🇮🇳', '🇨🇳', '🇪🇸', '🇮🇹', '🇷🇺', '🇰🇷', '🇲🇽', '🇳🇱'],
    'numbers': ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '🔢', '💯', '🎯', '⭐', '💎', '🏆'],
    'food': ['🍎', '🍌', '🍊', '🍇', '🍓', '🥝', '🍑', '🍒', '🥭', '🍍', '🥥', '🥑', '🍅', '🥕', '🌽', '🥒']
}
POWER_UPS = {'peek': '👀', 'time_freeze': '⏱️'}
DIFFICULTY_SETTINGS = {'easy': {'pairs': 6}, 'medium': {'pairs': 8}, 'hard': {'pairs': 12}}
ACHIEVEMENTS = {
    1: ("Speed Demon", "Finish a hard game in under 90 seconds.", "⚡️"),
    2: ("Perfectionist", "Finish any game with the minimum possible moves.", "🎯"),
    3: ("Theme Master", "Win a game with every available theme.", "🎨"),
    4: ("Streaker", "Win 3 games in a row.", "🔥")
}
games = {}

# --- DATABASE ---
def get_db_connection():
    conn = sqlite3.connect('memory_game.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN win_streak INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT UNIQUE NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, win_streak INTEGER DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS game_stats (id INTEGER PRIMARY KEY, user_id INTEGER, difficulty TEXT, theme TEXT, moves INTEGER, time_seconds INTEGER, completed_at TIMESTAMP, FOREIGN KEY (user_id) REFERENCES users (id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS achievements (id INTEGER PRIMARY KEY, name TEXT, description TEXT, icon TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_achievements (user_id INTEGER, achievement_id INTEGER, earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (user_id, achievement_id), FOREIGN KEY (user_id) REFERENCES users (id), FOREIGN KEY (achievement_id) REFERENCES achievements (id))''')
    for achievement_id, data in ACHIEVEMENTS.items():
        cursor.execute("INSERT OR IGNORE INTO achievements (id, name, description, icon) VALUES (?, ?, ?, ?)", (achievement_id, data[0], data[1], data[2]))
    conn.commit()
    conn.close()

def check_and_award_achievements(user_id, game_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (user_id,))
    earned_ids = {row['achievement_id'] for row in cursor.fetchall()}
    newly_earned = []

    def award_achievement(achievement_id):
        if achievement_id not in earned_ids:
            cursor.execute("INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)", (user_id, achievement_id))
            newly_earned.append(ACHIEVEMENTS[achievement_id])
            earned_ids.add(achievement_id)

    if game_data['difficulty'] == 'hard' and game_data['completion_time'] <= 90: award_achievement(1)
    if game_data['moves'] == game_data['pairs_needed']: award_achievement(2)

    cursor.execute("SELECT DISTINCT theme FROM game_stats WHERE user_id = ?", (user_id,))
    won_themes = {row['theme'] for row in cursor.fetchall()}
    if set(CARD_THEMES.keys()).issubset(won_themes): award_achievement(3)
            
    cursor.execute("UPDATE users SET win_streak = win_streak + 1 WHERE id = ?", (user_id,))
    cursor.execute("SELECT win_streak FROM users WHERE id = ?", (user_id,))
    streak = cursor.fetchone()
    if streak and streak['win_streak'] >= 3: award_achievement(4)

    conn.commit()
    conn.close()
    return newly_earned
    
def get_user_stats(user_id):
    conn = get_db_connection()
    data = conn.execute("SELECT COUNT(*) as games, SUM(moves) as total_moves, MIN(time_seconds) as best_time FROM game_stats WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    stats = {'games_played': 0, 'games_won': 0, 'win_rate': 0, 'total_moves': 0, 'average_moves': 0.0, 'best_time': None}
    if data and data['games'] > 0:
        games_played = data['games']
        total_moves = data['total_moves']
        stats.update({'games_played': games_played, 'games_won': games_played, 'win_rate': 100.0, 'total_moves': total_moves if total_moves else 0, 'average_moves': round(total_moves / games_played, 1) if total_moves and games_played > 0 else 0, 'best_time': data['best_time']})
    return stats

# --- VIEWS & API ROUTES ---
@app.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('login'))
    return render_template('index.html', themes=CARD_THEMES.keys(), difficulties=DIFFICULTY_SETTINGS.keys())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        conn = get_db_connection()
        try:
            password_hash = generate_password_hash(password)
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)', (username, email, password_hash))
            conn.commit()
            session['user_id'] = cursor.lastrowid
            session['username'] = username
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Username or email already exists')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/stats')
def stats():
    if 'user_id' not in session: return redirect(url_for('login'))
    user_stats = get_user_stats(session['user_id'])
    return render_template('stats.html', stats=user_stats)

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    conn = get_db_connection()
    conn.execute('DELETE FROM game_stats WHERE user_id = ?', (session['user_id'],))
    conn.execute('DELETE FROM user_achievements WHERE user_id = ?', (session['user_id'],))
    conn.execute('UPDATE users SET win_streak = 0 WHERE id = ?', (session['user_id'],))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Stats reset successfully'})

@app.route('/achievements')
def achievements():
    if 'user_id' not in session: return redirect(url_for('login'))
    conn = get_db_connection()
    all_achievements_rows = conn.execute("SELECT * FROM achievements ORDER BY id").fetchall()
    user_achievements_rows = conn.execute("SELECT achievement_id FROM user_achievements WHERE user_id = ?", (session['user_id'],)).fetchall()
    conn.close()
    user_achievements_ids = {row['achievement_id'] for row in user_achievements_rows}
    all_achievements = [dict(row) for row in all_achievements_rows]
    return render_template('achievements.html', all_achievements=all_achievements, user_achievements=user_achievements_ids)

# --- GAME LOGIC ---
def create_game_logic(difficulty, theme, daily_seed=None):
    if difficulty not in DIFFICULTY_SETTINGS: return {'error': 'Invalid difficulty'}
    if theme not in CARD_THEMES: return {'error': 'Invalid theme'}
    
    pairs_needed = DIFFICULTY_SETTINGS[difficulty]['pairs']
    rng = random.Random(daily_seed) if daily_seed else random
    
    selected_symbols = rng.sample(CARD_THEMES[theme], pairs_needed)
    cards = selected_symbols * 2
    rng.shuffle(cards)

    game_id = str(uuid.uuid4())
    games[game_id] = {
        'cards': cards, 'flipped': [False] * len(cards), 'matched': [False] * len(cards),
        'moves': 0, 'pairs_found': 0, 'pairs_needed': pairs_needed, 'difficulty': difficulty,
        'theme': theme, 'start_time': time.time(), 'completed': False, 'user_id': session['user_id'],
        'consecutive_matches': 0, # Track consecutive matches
        'earned_powerups': [] # Store earned powerups
    }
    
    return {'game_id': game_id, 'total_cards': len(cards), 'pairs_to_find': pairs_needed}

@app.route('/api/new-game', methods=['POST'])
def new_game():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    data = request.json
    return jsonify(create_game_logic(data.get('difficulty', 'easy'), data.get('theme', 'animals')))

@app.route('/api/daily-challenge', methods=['POST'])
def daily_challenge():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    today = date.today()
    seed = today.toordinal()
    theme_index = seed % len(CARD_THEMES)
    daily_theme = list(CARD_THEMES.keys())[theme_index]
    return jsonify(create_game_logic('medium', daily_theme, daily_seed=seed))

@app.route('/api/flip-card', methods=['POST'])
def flip_card():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    data = request.json
    game_id = data.get('game_id')
    card_index = data.get('card_index')
    if game_id not in games: return jsonify({'error': 'Game not found'}), 404
    game = games[game_id]
    if game['completed'] or card_index is None or not (0 <= card_index < len(game['cards'])): return jsonify({'error': 'Invalid request'}), 400
    if game['flipped'][card_index] or game['matched'][card_index]: return jsonify({'error': 'Card already active'}), 400
    
    game['flipped'][card_index] = True
    response_data = {'card_value': game['cards'][card_index]}

    flipped_indices = [i for i, is_flipped in enumerate(game['flipped']) if is_flipped and not game['matched'][i]]
    if len(flipped_indices) % 2 == 1: game['moves'] += 1

    if len(flipped_indices) == 2:
        idx1, idx2 = flipped_indices
        if game['cards'][idx1] == game['cards'][idx2]:
            game['matched'][idx1] = True; game['matched'][idx2] = True; game['pairs_found'] += 1
            game['consecutive_matches'] += 1
            response_data.update({'match': True, 'matched_indices': flipped_indices})

            if game['consecutive_matches'] == 2:
                earned_pu = random.choice(list(POWER_UPS.keys()))
                game['earned_powerups'].append(earned_pu)
                response_data['earned_powerup'] = earned_pu
                game['consecutive_matches'] = 0
        else:
            game['consecutive_matches'] = 0
            response_data.update({'match': False, 'flip_back': flipped_indices})
        
        game['flipped'][idx1] = False; game['flipped'][idx2] = False

    if game['pairs_found'] == game['pairs_needed']:
        game['completed'] = True
        completion_time = int(time.time() - game['start_time'])
        conn = get_db_connection()
        conn.execute("INSERT INTO game_stats (user_id, difficulty, theme, moves, time_seconds) VALUES (?, ?, ?, ?, ?)",
                     (game['user_id'], game['difficulty'], game['theme'], game['moves'], completion_time))
        conn.commit()
        conn.close()
        game_result_data = {**game, 'completion_time': completion_time}
        new_achievements = check_and_award_achievements(game['user_id'], game_result_data)
        response_data.update({'game_completed': True, 'completion_time': completion_time, 'final_moves': game['moves'], 'new_achievements': new_achievements})
    
    response_data.update({'moves': game['moves'], 'pairs_found': game['pairs_found']})
    return jsonify(response_data)

@app.route('/api/use-powerup', methods=['POST'])
def use_powerup():
    if 'user_id' not in session: return jsonify({'error': 'Not logged in'}), 401
    data = request.json
    game_id = data.get('game_id')
    powerup_type = data.get('powerup')
    if game_id not in games: return jsonify({'error': 'Game not found'}), 404
    game = games[game_id]
    if powerup_type not in game['earned_powerups']: return jsonify({'error': 'Power-up not available'}), 400
    
    game['earned_powerups'].remove(powerup_type)
    response_data = {'success': True, 'powerup_used': powerup_type}
    if powerup_type == 'peek':
        unflipped_indices = [i for i, card in enumerate(game['cards']) if not game['matched'][i] and not game['flipped'][i]]
        peek_indices = random.sample(unflipped_indices, min(len(unflipped_indices), 4))
        response_data['peek_indices'] = peek_indices
    return jsonify(response_data)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)