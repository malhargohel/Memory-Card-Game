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
        this.cardBackSelect = document.getElementById('card-back');
        
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

        // Sound Elements
        this.flipSound = document.getElementById('flip-sound');
        this.matchSound = document.getElementById('match-sound');
        this.winSound = document.getElementById('win-sound');
    }
    
    bindEvents() {
        this.newGameBtn.addEventListener('click', () => this.startNewGame());
        this.playAgainBtn.addEventListener('click', () => {
            this.hideModal();
            this.startNewGame();
        });
        this.closeModalBtn.addEventListener('click', () => this.hideModal());
        
        this.winModal.addEventListener('click', (e) => {
            if (e.target === this.winModal) this.hideModal();
        });
        
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.winModal.classList.contains('show')) {
                this.hideModal();
            }
        });
    }

    /**
     * UPDATED - Plays a sound, handling browser autoplay policies.
     * @param {HTMLAudioElement} soundElement The audio element to play.
     */
    async playSound(soundElement) {
        try {
            soundElement.currentTime = 0;
            await soundElement.play();
        } catch (error) {
            // This error is common if the user hasn't interacted with the page yet.
            // We can safely ignore it, as subsequent sounds will likely play.
            console.log("Could not play sound, likely requires user interaction first.", error);
        }
    }
    
    async startNewGame() {
        try {
            this.stopTimer();
            this.resetDisplay();
            
            const difficulty = this.difficultySelect.value;
            const theme = this.themeSelect.value;
            
            const response = await fetch('/api/new-game', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ difficulty, theme })
            });
            
            if (!response.ok) throw new Error('Failed to start new game');
            
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
        const cardBack = this.cardBackSelect.value;
        
        cards.forEach((card, index) => {
            const cardElement = this.createCardElement(index, cardBack);
            this.gameBoard.appendChild(cardElement);
        });
    }
    
    createCardElement(index, cardBack) {
        const card = document.createElement('div');
        card.className = 'card';
        if (cardBack !== 'default') {
            card.classList.add(cardBack);
        }
        card.dataset.index = index;
        card.textContent = '❓';
        
        card.addEventListener('click', () => this.handleCardClick(index, card));
        
        return card;
    }
    
    async handleCardClick(cardIndex, cardElement) {
        if (!this.isGameActive || this.isProcessing || cardElement.classList.contains('flipped') || cardElement.classList.contains('matched')) {
            return;
        }
        
        this.isProcessing = true;
        this.playSound(this.flipSound);

        try {
            const response = await fetch('/api/flip-card', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ game_id: this.gameId, card_index: cardIndex })
            });
            
            if (!response.ok) throw new Error('Failed to flip card');
            
            const data = await response.json();
            this.processFlipResponse(data, cardElement);
            
        } catch (error) {
            console.error('Error flipping card:', error);
            this.isProcessing = false; // Ensure processing is unlocked on error
        }
    }
    
    processFlipResponse(data, cardElement) {
        cardElement.textContent = data.card_value;
        cardElement.classList.add('flipped');
        
        this.movesCount.textContent = data.moves;
        this.pairsCount.textContent = data.pairs_found;
        
        if (data.match === true) {
            this.playSound(this.matchSound);
            setTimeout(() => {
                data.matched_indices.forEach(index => {
                    const card = this.gameBoard.querySelector(`[data-index="${index}"]`);
                    card.classList.remove('flipped');
                    card.classList.add('matched');
                });
                this.isProcessing = false;
            }, 600);
        } else if (data.match === false) {
            setTimeout(() => {
                data.flip_back.forEach(index => {
                    const card = this.gameBoard.querySelector(`[data-index="${index}"]`);
                    card.classList.remove('flipped');
                    card.textContent = '❓';
                });
                this.isProcessing = false;
            }, 1200);
        } else {
             this.isProcessing = false;
        }
        
        if (data.game_completed) {
            this.handleGameCompletion(data);
        }
    }
    
    handleGameCompletion(data) {
        this.isGameActive = false;
        this.stopTimer();
        this.playSound(this.winSound);
        
        this.finalMoves.textContent = data.final_moves;
        this.finalTime.textContent = this.formatTime(data.completion_time);
        this.finalDifficulty.textContent = this.difficultySelect.value.charAt(0).toUpperCase() + this.difficultySelect.value.slice(1);
        this.finalTheme.textContent = this.themeSelect.value.charAt(0).toUpperCase() + this.themeSelect.value.slice(1);
        
        this.showWinAnimation();
        setTimeout(() => this.showModal(), 500);
    }
    
    showWinAnimation() {
        const matchedCards = this.gameBoard.querySelectorAll('.matched');
        matchedCards.forEach((card, index) => {
            setTimeout(() => {
                card.style.animation = 'pulse 0.5s ease-in-out';
            }, index * 50);
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
    }
    
    hideModal() {
        this.winModal.classList.remove('show');
    }
}

const style = document.createElement('style');
style.textContent = `
    @keyframes pulse {
        0% { transform: scale(0.95); }
        50% { transform: scale(1.05); box-shadow: 0 0 20px rgba(76, 175, 80, 0.6); }
        100% { transform: scale(0.95); }
    }
`;
document.head.appendChild(style);

document.addEventListener('DOMContentLoaded', () => {
    new MemoryGame();
});
