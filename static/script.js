class MemoryGame {
    constructor() {
        this.gameId = null;
        this.flippedCards = [];
        this.isProcessing = false;
        
        this.initializeElements();
        this.setupEventListeners();
        this.startNewGame();
    }
    
    initializeElements() {
        this.gameBoard = document.getElementById('game-board');
        this.movesEl = document.getElementById('moves');
        this.pairsEl = document.getElementById('pairs');
        this.totalPairsEl = document.getElementById('total-pairs');
        this.difficultySelect = document.getElementById('difficulty');
        this.newGameBtn = document.getElementById('new-game-btn');
        this.winMessage = document.getElementById('win-message');
        this.finalMovesEl = document.getElementById('final-moves');
        this.playAgainBtn = document.getElementById('play-again-btn');
    }
    
    setupEventListeners() {
        this.newGameBtn.addEventListener('click', () => this.startNewGame());
        this.playAgainBtn.addEventListener('click', () => this.startNewGame());
    }
    
    async startNewGame() {
        const difficulty = this.difficultySelect.value;
        
        try {
            const response = await fetch('/api/new-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ difficulty })
            });
            
            const data = await response.json();
            this.gameId = data.game_id;
            
            this.createBoard(data.cards, difficulty);
            this.updateStats(0, 0, data.cards / 2);
            this.hideWinMessage();
            
        } catch (error) {
            console.error('Error starting new game:', error);
        }
    }
    
    createBoard(cardCount, difficulty) {
        this.gameBoard.innerHTML = '';
        this.gameBoard.className = `game-board ${difficulty}`;
        this.flippedCards = [];
        this.isProcessing = false;
        
        for (let i = 0; i < cardCount; i++) {
            const card = document.createElement('div');
            card.className = 'card';
            card.dataset.index = i;
            card.textContent = '?';
            card.addEventListener('click', () => this.flipCard(i));
            this.gameBoard.appendChild(card);
        }
    }
    
    async flipCard(index) {
        if (this.isProcessing) return;
        
        const card = this.gameBoard.children[index];
        if (card.classList.contains('flipped') || card.classList.contains('matched')) {
            return;
        }
        
        try {
            const response = await fetch('/api/flip-card', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    game_id: this.gameId,
                    card_index: index
                })
            });
            
            const data = await response.json();
            
            if (data.error) {
                console.error('Error flipping card:', data.error);
                return;
            }
            
            // Show the card
            card.textContent = data.symbol;
            card.classList.add('flipped');
            this.flippedCards.push(index);
            
            // Update stats
            this.updateStats(data.moves, data.pairs_found, data.total_pairs);
            
            // Handle two cards flipped
            if (data.flipped_cards === 2) {
                this.isProcessing = true;
                
                setTimeout(() => {
                    if (data.match) {
                        // Mark cards as matched
                        this.flippedCards.forEach(cardIndex => {
                            const cardEl = this.gameBoard.children[cardIndex];
                            cardEl.classList.remove('flipped');
                            cardEl.classList.add('matched');
                        });
                    } else {
                        // Flip cards back
                        this.flippedCards.forEach(cardIndex => {
                            const cardEl = this.gameBoard.children[cardIndex];
                            cardEl.classList.remove('flipped');
                            cardEl.textContent = '?';
                        });
                    }
                    
                    this.flippedCards = [];
                    this.isProcessing = false;
                    
                    // Check for game over
                    if (data.game_over) {
                        this.showWinMessage(data.moves);
                    }
                }, 1000);
            }
            
        } catch (error) {
            console.error('Error flipping card:', error);
        }
    }
    
    updateStats(moves, pairs, totalPairs) {
        this.movesEl.textContent = moves;
        this.pairsEl.textContent = pairs;
        this.totalPairsEl.textContent = totalPairs;
    }
    
    showWinMessage(moves) {
        this.finalMovesEl.textContent = moves;
        this.winMessage.classList.remove('hidden');
    }
    
    hideWinMessage() {
        this.winMessage.classList.add('hidden');
    }
}

// Start the game when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new MemoryGame();
});