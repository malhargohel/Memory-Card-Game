class MemoryGame {
    constructor() {
        this.gameId = null;
        this.timer = null;
        this.startTime = null;
        this.elapsedTime = 0;
        this.isGameActive = false;
        this.flippedCards = [];
        this.isProcessing = false;
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        // Game controls
        this.newGameBtn = document.getElementById('new-game-btn');
        this.difficultySelect = document.getElementById('difficulty');
        this.themeSelect = document.getElementById('theme');
        
        // Game info displays
        this.movesCount = document.getElementById('moves-count');
        this.pairsCount = document.getElementById('pairs-count');
        this.pairsTotal = document.getElementById('pairs-total');
        this.timerDisplay = document.getElementById('timer');
        
        // Game board
        this.gameBoard = document.getElementById('game-board');
        
        // Modal elements
        this.winModal = document.getElementById('win-modal');
        this.finalMoves = document.getElementById('final-moves');
        this.finalTime = document.getElementById('final-time');
        this.finalDifficulty = document.getElementById('final-difficulty');
        this.finalTheme = document.getElementById('final-theme');
        this.playAgainBtn = document.getElementById('play-again-btn');
        this.closeModalBtn = document.getElementById('close-modal-btn');
    }
    
    bindEvents() {
        this.newGameBtn.addEventListener('click', () => this.startNewGame());
        this.playAgainBtn.addEventListener('click', () => {
            this.hideModal();
            this.startNewGame();
        });
        this.closeModalBtn.addEventListener('click', () => this.hideModal());
        
        // Close modal when clicking outside
        this.winModal.addEventListener('click', (e) => {
            if (e.target === this.winModal) {
                this.hideModal();
            }
        });
        
        // Keyboard controls
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.winModal.classList.contains('show')) {
                this.hideModal();
            }
        });
    }
    
    async startNewGame() {
        try {
            this.stopTimer();
            this.resetDisplay();
            
            const difficulty = this.difficultySelect.value;
            const theme = this.themeSelect.value;
            
            const response = await fetch('/api/new-game', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ difficulty, theme })
            });
            
            if (!response.ok) {
                throw new Error('Failed to start new game');
            }
            
            const data = await response.json();
            this.gameId = data.game_id;
            this.setupGameBoard(data.cards, data.grid);
            this.pairsTotal.textContent = data.cards.length / 2;
            this.startTimer();
            this.isGameActive = true;
            
        } catch (error) {
            console.error('Error starting new game:', error);
            alert('Failed to start new game. Please try again.');
        }
    }
    
    setupGameBoard(cards, gridType) {
        this.gameBoard.innerHTML = '';
        this.gameBoard.className = `game-board grid-${gridType}`;
        
        cards.forEach((card, index) => {
            const cardElement = this.createCardElement(card, index);
            this.gameBoard.appendChild(cardElement);
        });
    }
    
    createCardElement(cardValue, index) {
        const card = document.createElement('div');
        card.className = 'card';
        card.dataset.index = index;
        card.textContent = cardValue;
        
        card.addEventListener('click', () => this.handleCardClick(index, card));
        
        return card;
    }
    
    async handleCardClick(cardIndex, cardElement) {
        if (!this.isGameActive || this.isProcessing || 
            cardElement.classList.contains('flipped') || 
            cardElement.classList.contains('matched')) {
            return;
        }
        
        try {
            this.isProcessing = true;
            
            const response = await fetch('/api/flip-card', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    game_id: this.gameId,
                    card_index: cardIndex
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to flip card');
            }
            
            const data = await response.json();
            this.processFlipResponse(data, cardIndex, cardElement);
            
        } catch (error) {
            console.error('Error flipping card:', error);
        } finally {
            this.isProcessing = false;
        }
    }
    
    processFlipResponse(data, cardIndex, cardElement) {
        // Update card display
        cardElement.textContent = data.card_value;
        cardElement.classList.add('flipped', 'flip-animation');
        
        // Update game info
        this.movesCount.textContent = data.moves;
        this.pairsCount.textContent = data.pairs_found;
        
        // Handle matches
        if (data.match === true && data.matched_indices) {
            setTimeout(() => {
                data.matched_indices.forEach(index => {
                    const card = this.gameBoard.children[index];
                    card.classList.remove('flipped');
                    card.classList.add('matched');
                });
            }, 600);
        } else if (data.match === false && data.flip_back) {
            setTimeout(() => {
                data.flip_back.forEach(index => {
                    const card = this.gameBoard.children[index];
                    card.classList.remove('flipped', 'flip-animation');
                    card.textContent = '❓';
                });
            }, 1500);
        }
        
        // Check for game completion
        if (data.game_completed) {
            setTimeout(() => this.handleGameCompletion(data), 1000);
        }
    }
    
    handleGameCompletion(data) {
        this.isGameActive = false;
        this.stopTimer();
        
        // Update modal with results
        this.finalMoves.textContent = data.final_moves;
        this.finalTime.textContent = this.formatTime(data.completion_time);
        this.finalDifficulty.textContent = this.difficultySelect.value.charAt(0).toUpperCase() + this.difficultySelect.value.slice(1);
        this.finalTheme.textContent = this.themeSelect.value.charAt(0).toUpperCase() + this.themeSelect.value.slice(1);
        
        // Show celebration animation
        this.showWinAnimation();
        
        setTimeout(() => this.showModal(), 1000);
    }
    
    showWinAnimation() {
        // Add celebration effect to all matched cards
        const matchedCards = this.gameBoard.querySelectorAll('.matched');
        matchedCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.animation = 'pulse 0.5s ease-in-out';
            }, index * 100);
        });
    }
    
    startTimer() {
        this.startTime = Date.now();
        this.elapsedTime = 0;
        this.updateTimerDisplay();
        
        this.timer = setInterval(() => {
            this.elapsedTime = Math.floor((Date.now() - this.startTime) / 1000);
            this.updateTimerDisplay();
        }, 1000);
    }
    
    stopTimer() {
        if (this.timer) {
            clearInterval(this.timer);
            this.timer = null;
        }
    }
    
    updateTimerDisplay() {
        this.timerDisplay.textContent = this.formatTime(this.elapsedTime);
    }
    
    formatTime(seconds) {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
    }
    
    resetDisplay() {
        this.movesCount.textContent = '0';
        this.pairsCount.textContent = '0';
        this.pairsTotal.textContent = '0';
        this.timerDisplay.textContent = '00:00';
        this.gameBoard.innerHTML = '';
        this.elapsedTime = 0;
    }
    
    showModal() {
        this.winModal.classList.add('show');
        this.winModal.style.display = 'flex';
    }
    
    hideModal() {
        this.winModal.classList.remove('show');
        setTimeout(() => {
            this.winModal.style.display = 'none';
        }, 300);
    }
}

// Theme preview functionality
class ThemePreview {
    constructor() {
        this.themeSelect = document.getElementById('theme');
        this.bindEvents();
    }
    
    bindEvents() {
        this.themeSelect.addEventListener('change', () => {
            this.showThemePreview();
        });
    }
    
    showThemePreview() {
        // You could add a preview of the theme here
        // For now, we'll just update the select styling
        const selectedTheme = this.themeSelect.value;
        this.themeSelect.style.background = this.getThemeColor(selectedTheme);
    }
    
    getThemeColor(theme) {
        const colors = {
            'animals': 'linear-gradient(135deg, #4CAF50, #8BC34A)',
            'flags': 'linear-gradient(135deg, #2196F3, #03A9F4)',
            'numbers': 'linear-gradient(135deg, #FF9800, #FFC107)',
            'food': 'linear-gradient(135deg, #E91E63, #F06292)'
        };
        return colors[theme] || '';
    }
}

// Keyboard shortcuts
class KeyboardControls {
    constructor(game) {
        this.game = game;
        this.bindEvents();
    }
    
    bindEvents() {
        document.addEventListener('keydown', (e) => {
            // Prevent shortcuts when typing in inputs
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') {
                return;
            }
            
            switch(e.key.toLowerCase()) {
                case 'n':
                    e.preventDefault();
                    this.game.startNewGame();
                    break;
                case ' ':
                    e.preventDefault();
                    if (!this.game.isGameActive) {
                        this.game.startNewGame();
                    }
                    break;
                case '1':
                case '2':
                case '3':
                    e.preventDefault();
                    const difficulties = ['easy', 'medium', 'hard'];
                    this.game.difficultySelect.value = difficulties[parseInt(e.key) - 1];
                    break;
            }
        });
    }
}

// Performance monitoring
class GameAnalytics {
    constructor() {
        this.gameStats = {
            gamesPlayed: 0,
            totalMoves: 0,
            totalTime: 0,
            bestTime: Infinity,
            bestMoves: Infinity
        };
        this.loadStats();
    }
    
    recordGame(moves, time, difficulty, theme) {
        this.gameStats.gamesPlayed++;
        this.gameStats.totalMoves += moves;
        this.gameStats.totalTime += time;
        
        if (time < this.gameStats.bestTime) {
            this.gameStats.bestTime = time;
        }
        
        if (moves < this.gameStats.bestMoves) {
            this.gameStats.bestMoves = moves;
        }
        
        this.saveStats();
    }
    
    loadStats() {
        const saved = localStorage.getItem('memoryGameStats');
        if (saved) {
            this.gameStats = { ...this.gameStats, ...JSON.parse(saved) };
        }
    }
    
    saveStats() {
        localStorage.setItem('memoryGameStats', JSON.stringify(this.gameStats));
    }
}

// Add CSS for pulse animation
const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); box-shadow: 0 0 20px rgba(76, 175, 80, 0.6); }
        100% { transform: scale(1); }
    }
`;
document.head.appendChild(style);

// Initialize the game when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const game = new MemoryGame();
    const themePreview = new ThemePreview();
    const keyboardControls = new KeyboardControls(game);
    const analytics = new GameAnalytics();
    
    // Make analytics available globally for game completion tracking
    window.gameAnalytics = analytics;
});