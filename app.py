from flask import Flask, render_template, jsonify, request
import random
import json

app = Flask(__name__)

# Game state storage (in production, use a database)
games = {}

# Card symbols for the memory game
CARD_SYMBOLS = ['🐶', '🐱', '🐭', '🐹', '🐰', '🦊', '🐻', '🐼', '🐨', '🐯', '🦁', '🐮', '🐷', '🐸', '🐵', '🐔']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/new-game', methods=['POST'])
def new_game():
    data = request.json
    difficulty = data.get('difficulty', 'easy')
    
    # Set grid size based on difficulty
    if difficulty == 'easy':
        pairs = 6  # 4x3 grid
    elif difficulty == 'medium':
        pairs = 8  # 4x4 grid
    else:  # hard
        pairs = 12  # 4x6 grid
    
    # Create pairs of cards
    symbols = random.sample(CARD_SYMBOLS, pairs)
    cards = symbols * 2  # Create pairs
    random.shuffle(cards)
    
    game_id = str(random.randint(1000, 9999))
    
    games[game_id] = {
        'cards': cards,
        'flipped': [False] * len(cards),
        'matched': [False] * len(cards),
        'moves': 0,
        'pairs_found': 0,
        'total_pairs': pairs,
        'difficulty': difficulty
    }
    
    return jsonify({
        'game_id': game_id,
        'cards': len(cards),
        'difficulty': difficulty
    })

@app.route('/api/flip-card', methods=['POST'])
def flip_card():
    data = request.json
    game_id = data['game_id']
    card_index = data['card_index']
    
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    
    # Don't flip if already matched or flipped
    if game['matched'][card_index] or game['flipped'][card_index]:
        return jsonify({'error': 'Card already flipped or matched'}), 400
    
    # Flip the card
    game['flipped'][card_index] = True
    
    # Check how many cards are currently flipped
    flipped_indices = [i for i, flipped in enumerate(game['flipped']) if flipped and not game['matched'][i]]
    
    result = {
        'symbol': game['cards'][card_index],
        'flipped_cards': len(flipped_indices),
        'game_over': False,
        'match': False
    }
    
    # If two cards are flipped, check for match
    if len(flipped_indices) == 2:
        game['moves'] += 1
        card1_idx, card2_idx = flipped_indices
        
        if game['cards'][card1_idx] == game['cards'][card2_idx]:
            # Match found!
            game['matched'][card1_idx] = True
            game['matched'][card2_idx] = True
            game['pairs_found'] += 1
            result['match'] = True
            
            # Check if game is complete
            if game['pairs_found'] == game['total_pairs']:
                result['game_over'] = True
        
        # Reset flipped status for non-matched cards
        for i in range(len(game['flipped'])):
            if not game['matched'][i]:
                game['flipped'][i] = False
    
    result['moves'] = game['moves']
    result['pairs_found'] = game['pairs_found']
    result['total_pairs'] = game['total_pairs']
    
    return jsonify(result)

@app.route('/api/game-state/<game_id>')
def get_game_state(game_id):
    if game_id not in games:
        return jsonify({'error': 'Game not found'}), 404
    
    game = games[game_id]
    return jsonify({
        'moves': game['moves'],
        'pairs_found': game['pairs_found'],
        'total_pairs': game['total_pairs'],
        'difficulty': game['difficulty'],
        'matched': game['matched']
    })

if __name__ == '__main__':
    app.run(debug=True)