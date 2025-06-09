from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
import random
import time
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here-change-this-to-something-random')

# Card themes
CARD_THEMES = {
    'animals': ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐸', '🐵', '🦁', '🐯', '🐨', '🐷', '🐮', '🦄'],
    'flags': ['🇺🇸', '🇬🇧', '🇫🇷', '🇩🇪', '🇯🇵', '🇨🇦', '🇦🇺', '🇧🇷', '🇮🇳', '🇨🇳', '🇪🇸', '🇮🇹', '🇷🇺', '🇰🇷', '🇲🇽', '🇳🇱'],
    'numbers': ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟', '🔢', '💯', '🎯', '⭐', '💎', '🏆'],
    'food': ['🍎', '🍌', '🍊', '🍇', '🍓', '🥝', '🍑', '🍒', '🥭', '🍍', '🥥', '🥑', '🍅', '🥕', '🌽', '🥒']
}

# Difficulty settings
DIFFICULTY_SETTINGS = {
    'easy': {'pairs': 6, 'grid': '4x3'},
    'medium': {'pairs': 8, 'grid': '4x4'},
    'hard': {'pairs': 12, 'grid': '6x4'}
}

# In-memory game storage (use Redis or database in production)
games = {}

def init_db():
    """Initialize SQLite database for user accounts and statistics"""
    conn = sqlite3.connect('memory_game.db')
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Game statistics table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            difficulty TEXT NOT NULL,
            theme TEXT NOT NULL,
            moves INTEGER NOT NULL,
            time_seconds INTEGER NOT NULL,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_user_stats(user_id):
    """Get aggregated user statistics from the database."""
    conn = sqlite3.connect('memory_game.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*),
            SUM(moves),
            MIN(time_seconds)
        FROM game_stats 
        WHERE user_id = ?
    ''', (user_id,))
    
    data = cursor.fetchone()
    conn.close()
    
    stats = {
        'games_played': 0,
        'games_won': 0,
        'win_rate': 0,
        'total_moves': 0,
        'average_moves': 0,
        'best_time': None
    }
    
    if data and data[0] > 0:
        games_played = data[0]
        total_moves = data[1]
        best_time = data[2]
        
        # Since we only record wins, games_played is the same as games_won
        stats['games_played'] = games_played
        stats['games_won'] = games_played
        stats['win_rate'] = 100.0
        stats['total_moves'] = total_moves
        stats['average_moves'] = round(total_moves / games_played, 1) if games_played > 0 else 0
        stats['best_time'] = best_time
        
    return stats


def save_game_result(user_id, difficulty, theme, moves, time_seconds):
    """Save game result to database"""
    conn = sqlite3.connect('memory_game.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO game_stats (user_id, difficulty, theme, moves, time_seconds)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, difficulty, theme, moves, time_seconds))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', themes=CARD_THEMES.keys(), difficulties=DIFFICULTY_SETTINGS.keys())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('memory_game.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, password_hash, username FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = user[2]
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
        
        conn = sqlite3.connect('memory_game.db')
        cursor = conn.cursor()
        
        try:
            password_hash = generate_password_hash(password)
            cursor.execute('INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)',
                         (username, email, password_hash))
            conn.commit()
            user_id = cursor.lastrowid
            session['user_id'] = user_id
            session['username'] = username
            conn.close()
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Username or email already exists')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """Clear the user session and redirect to login page"""
    session.clear()
    return redirect(url_for('login'))

@app.route('/stats')
def stats():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_stats = get_user_stats(session['user_id'])
    return render_template('stats.html', stats=user_stats)

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    """Reset all game statistics for the logged-in user from the database."""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    user_id = session['user_id']
    conn = sqlite3.connect('memory_game.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM game_stats WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True, 'message': 'Stats reset successfully'})

@app.route('/api/new-game', methods=['POST'])
def new_game():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    difficulty = data.get('difficulty', 'easy')
    theme = data.get('theme', 'animals')
    
    if difficulty not in DIFFICULTY_SETTINGS:
        return jsonify({'error': 'Invalid difficulty'}), 400
    
    if theme not in CARD_THEMES:
        return jsonify({'error': 'Invalid theme'}), 400
    
    game_id = str(uuid.uuid4())
    pairs_needed = DIFFICULTY_SETTINGS[difficulty]['pairs']
    
    available_symbols = CARD_THEMES[theme]
    selected_symbols = random.sample(available_symbols, pairs_needed)
    
    cards = selected_symbols * 2
    random.shuffle(cards)
    
    games[game_id] = {
        'cards': cards,
        'flipped': [False] * len(cards),
        'matched': [False] * len(cards),
        'moves': 0,
        'pairs_found': 0,
        'pairs_needed': pairs_needed,
        'difficulty': difficulty,
        'theme': theme,
        'start_time': time.time(),
        'completed': False,
        'user_id': session['user_id']
    }
    
    return jsonify({
        'game_id': game_id,
        'cards': ['❓'] * len(cards),
        'grid': DIFFICULTY_SETTINGS[difficulty]['grid']
    })

@app.route('/api/flip-card', methods=['POST'])
def flip_card():
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    data = request.json
    game_id = data.get('game_id')
    card_index = data.get('card_index')
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    
    if game['user_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 401
    
    if game['completed'] or card_index is None or card_index < 0 or card_index >= len(game['cards']):
        return jsonify({'error': 'Invalid request'}), 400
    
    if game['flipped'][card_index] or game['matched'][card_index]:
        return jsonify({'error': 'Card already active'}), 400
    
    game['flipped'][card_index] = True
    
    response_data = { 'card_value': game['cards'][card_index] }
    
    flipped_indices = [i for i, is_flipped in enumerate(game['flipped']) if is_flipped and not game['matched'][i]]
    
    if len(flipped_indices) % 2 == 1:
        game['moves'] += 1 # A move is a pair of flips

    if len(flipped_indices) == 2:
        idx1, idx2 = flipped_indices
        if game['cards'][idx1] == game['cards'][idx2]:
            game['matched'][idx1] = True
            game['matched'][idx2] = True
            game['pairs_found'] += 1
            response_data['match'] = True
            response_data['matched_indices'] = flipped_indices
        else:
            response_data['match'] = False
            response_data['flip_back'] = flipped_indices
        
        game['flipped'][idx1] = False
        game['flipped'][idx2] = False

    if game['pairs_found'] == game['pairs_needed']:
        game['completed'] = True
        completion_time = int(time.time() - game['start_time'])
        save_game_result(game['user_id'], game['difficulty'], game['theme'], game['moves'], completion_time)
        response_data.update({
            'game_completed': True,
            'completion_time': completion_time,
            'final_moves': game['moves']
        })

    response_data.update({
        'moves': game['moves'],
        'pairs_found': game['pairs_found']
    })
    
    return jsonify(response_data)

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)