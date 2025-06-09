from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import uuid
import random
import time
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-this-to-something-random'

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
    """Get user statistics from database"""
    conn = sqlite3.connect('memory_game.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as games_played,
            AVG(moves) as avg_moves,
            AVG(time_seconds) as avg_time,
            MIN(moves) as best_moves,
            MIN(time_seconds) as best_time,
            difficulty,
            theme
        FROM game_stats 
        WHERE user_id = ?
        GROUP BY difficulty, theme
    ''', (user_id,))
    
    stats = cursor.fetchall()
    conn.close()
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

def update_game_stats(won=False, moves=0, time_taken=None):
    """Update game statistics in session"""
    if 'game_stats' not in session:
        session['game_stats'] = {
            'games_played': 0,
            'games_won': 0,
            'total_moves': 0,
            'best_time': None,
            'average_moves': 0,
            'win_rate': 0
        }
    
    stats = session['game_stats']
    
    # Update basic stats
    stats['games_played'] += 1
    stats['total_moves'] += moves
    
    if won:
        stats['games_won'] += 1
        
        # Update best time if this is better
        if time_taken:
            if stats['best_time'] is None or time_taken < stats['best_time']:
                stats['best_time'] = time_taken
    
    # Calculate derived stats
    if stats['games_played'] > 0:
        stats['win_rate'] = round((stats['games_won'] / stats['games_played']) * 100, 1)
        stats['average_moves'] = round(stats['total_moves'] / stats['games_played'], 1)
    
    session['game_stats'] = stats
    session.modified = True

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
        cursor.execute('SELECT id, password_hash FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
        
        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
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

@app.route('/api/stats')
def api_stats():
    """Return game statistics as JSON"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    # Get stats from session or initialize empty stats
    game_stats = session.get('game_stats', {
        'games_played': 0,
        'games_won': 0,
        'total_moves': 0,
        'best_time': None,
        'average_moves': 0,
        'win_rate': 0
    })
    
    return jsonify(game_stats)

@app.route('/reset_stats', methods=['POST'])
def reset_stats():
    """Reset all game statistics"""
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    session['game_stats'] = {
        'games_played': 0,
        'games_won': 0,
        'total_moves': 0,
        'best_time': None,
        'average_moves': 0,
        'win_rate': 0
    }
    session.modified = True
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
    
    # Select random symbols from the chosen theme
    available_symbols = CARD_THEMES[theme]
    selected_symbols = random.sample(available_symbols, pairs_needed)
    
    # Create pairs and shuffle
    cards = selected_symbols * 2
    random.shuffle(cards)
    
    # Initialize game state
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
        'cards': ['❓'] * len(cards),  # Hide cards initially
        'difficulty': difficulty,
        'theme': theme,
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
    
    if game['completed']:
        return jsonify({'error': 'Game already completed'}), 400
    
    if card_index < 0 or card_index >= len(game['cards']):
        return jsonify({'error': 'Invalid card index'}), 400
    
    if game['flipped'][card_index] or game['matched'][card_index]:
        return jsonify({'error': 'Card already flipped or matched'}), 400
    
    # Flip the card
    game['flipped'][card_index] = True
    game['moves'] += 1
    
    # Check for matches
    flipped_indices = [i for i, flipped in enumerate(game['flipped']) if flipped and not game['matched'][i]]
    
    response_data = {
        'card_value': game['cards'][card_index],
        'moves': game['moves'],
        'pairs_found': game['pairs_found']
    }
    
    if len(flipped_indices) == 2:
        # Check if the two flipped cards match
        if game['cards'][flipped_indices[0]] == game['cards'][flipped_indices[1]]:
            # Match found
            game['matched'][flipped_indices[0]] = True
            game['matched'][flipped_indices[1]] = True
            game['pairs_found'] += 1
            response_data['match'] = True
            response_data['matched_indices'] = flipped_indices
            response_data['pairs_found'] = game['pairs_found']
        else:
            # No match
            response_data['match'] = False
            response_data['flip_back'] = flipped_indices
        
        # Reset flipped state for non-matched cards
        for i in flipped_indices:
            if not game['matched'][i]:
                game['flipped'][i] = False
    
    # Check if game is completed
    if game['pairs_found'] == game['pairs_needed']:
        game['completed'] = True
        completion_time = int(time.time() - game['start_time'])
        
        # Save game result to database
        save_game_result(
            game['user_id'],
            game['difficulty'],
            game['theme'],
            game['moves'],
            completion_time
        )
        
        # Update session stats
        update_game_stats(won=True, moves=game['moves'], time_taken=completion_time)
        
        response_data['game_completed'] = True
        response_data['completion_time'] = completion_time
        response_data['final_moves'] = game['moves']
    
    return jsonify(response_data)

@app.route('/api/game-state/<game_id>')
def get_game_state(game_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    
    if game['user_id'] != session['user_id']:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Return visible cards (matched cards show their value, others show ❓)
    visible_cards = []
    for i, card in enumerate(game['cards']):
        if game['matched'][i]:
            visible_cards.append(card)
        else:
            visible_cards.append('❓')
    
    current_time = int(time.time() - game['start_time']) if not game['completed'] else None
    
    return jsonify({
        'cards': visible_cards,
        'moves': game['moves'],
        'pairs_found': game['pairs_found'],
        'pairs_needed': game['pairs_needed'],
        'completed': game['completed'],
        'elapsed_time': current_time,
        'difficulty': game['difficulty'],
        'theme': game['theme']
    })

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False)