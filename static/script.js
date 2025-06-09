class MemoryGame {
    constructor() {
        this.gameId = null;
        this.timer = null;
        this.timerFrozen = false;
        this.isGameActive = false;
        this.isProcessing = false;
        this.initializeElements();
        this.bindEvents();
    }
    initializeElements() {
        this.newGameBtn = document.getElementById('new-game-btn');
        this.dailyChallengeBtn = document.getElementById('daily-challenge-btn');
        this.difficultySelect = document.getElementById('difficulty');
        this.themeSelect = document.getElementById('theme');
        this.cardBackSelect = document.getElementById('card-back');
        this.movesCount = document.getElementById('moves-count');
        this.pairsCount = document.getElementById('pairs-count');
        this.pairsTotal = document.getElementById('pairs-total');
        this.timerDisplay = document.getElementById('timer');
        this.gameBoard = document.getElementById('game-board');
        this.winModal = document.getElementById('win-modal');
        this.winModalTitle = document.getElementById('win-modal-title');
        this.finalMoves = document.getElementById('final-moves');
        this.finalTime = document.getElementById('final-time');
        this.finalDifficulty = document.getElementById('final-difficulty');
        this.finalTheme = document.getElementById('final-theme');
        this.achievementsContainer = document.getElementById('new-achievements-container');
        this.achievementsList = document.getElementById('new-achievements-list');
        this.playAgainBtn = document.getElementById('play-again-btn');
        this.flipSound = document.getElementById('flip-sound');
        this.matchSound = document.getElementById('match-sound');
        this.winSound = document.getElementById('win-sound');
        this.howToPlayBtn = document.getElementById('how-to-play-btn');
        this.infoModal = document.getElementById('info-modal');
        this.closeInfoModalBtn = document.getElementById('close-info-modal-btn');
        this.toastNotification = document.getElementById('toast-notification');
        this.powerUpTray = document.getElementById('power-up-tray');
    }
    bindEvents() {
        this.newGameBtn.addEventListener('click', () => this.startNewGame(false));
        this.dailyChallengeBtn.addEventListener('click', () => this.startNewGame(true));
        this.playAgainBtn.addEventListener('click', () => {
            this.hideModal(this.winModal);
            this.startNewGame();
        });
        document.getElementById('close-modal-btn').addEventListener('click', () => this.hideModal(this.winModal));
        this.howToPlayBtn.addEventListener('click', () => this.showModal(this.infoModal));
        this.closeInfoModalBtn.addEventListener('click', () => this.hideModal(this.infoModal));
    }
    async startNewGame(isDaily = false) {
        this.stopTimer();
        this.resetDisplay();
        this.isGameActive = true;
        this.isProcessing = true;
        const endpoint = isDaily ? '/api/daily-challenge' : '/api/new-game';
        const payload = isDaily ? {} : { difficulty: this.difficultySelect.value, theme: this.themeSelect.value };
        this.winModalTitle.textContent = isDaily ? "🌟 Daily Challenge Complete!" : "🎉 Congratulations!";
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!response.ok) throw new Error('Failed to start game');
            const data = await response.json();
            this.gameId = data.game_id;
            this.setupGameBoard(data);
            this.startTimer();
        } catch (error) {
            console.error('Error starting new game:', error);
            alert('Failed to start new game. Please try again.');
        } finally {
            this.isProcessing = false;
        }
    }
    setupGameBoard(gameData) {
        this.gameBoard.innerHTML = '';
        this.pairsTotal.textContent = gameData.pairs_to_find;
        const totalCards = gameData.total_cards;
        let columns = Math.ceil(Math.sqrt(totalCards));
        if (columns > 6) columns = 6;
        if (totalCards === 14) columns = 5;
        this.gameBoard.style.gridTemplateColumns = `repeat(${columns}, 1fr)`;
        for (let i = 0; i < totalCards; i++) {
            this.gameBoard.appendChild(this.createCardElement(i));
        }
    }
    createCardElement(index) {
        const card = document.createElement('div');
        card.className = 'card';
        const cardBack = this.cardBackSelect.value;
        if (cardBack !== 'default') card.classList.add(cardBack);
        card.dataset.index = index;
        card.textContent = '❓';
        card.addEventListener('click', () => this.handleCardClick(index, card));
        return card;
    }
    async handleCardClick(cardIndex, cardElement) {
        if (!this.isGameActive || this.isProcessing || cardElement.classList.contains('flipped') || cardElement.classList.contains('matched')) return;
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
            this.isProcessing = false;
        }
    }
    processFlipResponse(data, cardElement) {
        cardElement.textContent = data.card_value;
        cardElement.classList.add('flipped');
        this.movesCount.textContent = data.moves;
        this.pairsCount.textContent = data.pairs_found;
        if (data.earned_powerup) {
            this.addPowerUpToTray(data.earned_powerup);
            this.showNotification(`✨ Power-up Earned!`);
        }
        if (data.match === true) {
            this.playSound(this.matchSound);
            setTimeout(() => data.matched_indices.forEach(index => this.gameBoard.querySelector(`[data-index="${index}"]`).classList.add('matched')), 600);
        } else if (data.match === false) {
            setTimeout(() => {
                data.flip_back.forEach(index => {
                    const cardToFlipBack = this.gameBoard.querySelector(`[data-index="${index}"]`);
                    if (cardToFlipBack) {
                        cardToFlipBack.classList.remove('flipped');
                        cardToFlipBack.textContent = '❓';
                    }
                });
            }, 1200);
        }
        if (!data.game_completed) {
            setTimeout(() => { this.isProcessing = false; }, data.match === false ? 1200 : 600);
        }
        if (data.game_completed) this.handleGameCompletion(data);
    }
    addPowerUpToTray(powerupType) {
        const powerUpBtn = document.createElement('button');
        powerUpBtn.className = 'btn btn-special power-up-btn';
        powerUpBtn.dataset.type = powerupType;
        powerUpBtn.textContent = powerupType === 'peek' ? '👀' : '⏱️';
        powerUpBtn.onclick = () => this.usePowerUp(powerUpBtn);
        this.powerUpTray.appendChild(powerUpBtn);
    }
    async usePowerUp(buttonElement) {
        const powerupType = buttonElement.dataset.type;
        buttonElement.disabled = true;
        try {
            const response = await fetch('/api/use-powerup', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ game_id: this.gameId, powerup: powerupType })
            });
            const data = await response.json();
            if (data.success) {
                this.applyPowerUpEffect(data);
                buttonElement.remove();
            } else {
                buttonElement.disabled = false;
                this.showNotification("Couldn't use power-up. Please try again.");
            }
        } catch (error) {
            console.error("Error using power-up", error);
            buttonElement.disabled = false;
        }
    }
    applyPowerUpEffect(data) {
        const powerupType = data.powerup_used;
        if (powerupType === 'peek') {
            this.showNotification('👀 Peek! Revealing cards...');
            data.peek_indices.forEach(index => {
                const peekCard = this.gameBoard.querySelector(`[data-index="${index}"]`);
                if (peekCard) {
                    peekCard.classList.add('peek');
                    setTimeout(() => { peekCard.classList.remove('peek'); }, 2000);
                }
            });
        } else if (powerupType === 'time_freeze') {
            this.showNotification('⏱️ Time Freeze! Timer paused for 5 seconds.');
            this.freezeTimer(5);
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
        if (data.new_achievements && data.new_achievements.length > 0) {
            this.achievementsList.innerHTML = data.new_achievements.map(ach => `<div class="achievement-unlocked"><span class="icon">${ach[2]}</span><span>${ach[0]}: ${ach[1]}</span></div>`).join('');
            this.achievementsContainer.style.display = 'block';
        }
        setTimeout(() => this.showModal(this.winModal), 800);
    }
    async playSound(soundElement) {
        try {
            soundElement.currentTime = 0;
            await soundElement.play();
        } catch (err) { console.log("Could not play sound.", err); }
    }
    startTimer() {
        let startTime = Date.now();
        this.timer = setInterval(() => {
            if (this.timerFrozen) return;
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            this.timerDisplay.textContent = this.formatTime(elapsed);
        }, 1000);
    }
    stopTimer() { clearInterval(this.timer); this.timer = null; }
    freezeTimer(seconds) {
        this.timerFrozen = true;
        this.timerDisplay.classList.add('frozen');
        setTimeout(() => { this.timerFrozen = false; this.timerDisplay.classList.remove('frozen'); }, seconds * 1000);
    }
    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    resetDisplay() {
        this.movesCount.textContent = '0';
        this.pairsCount.textContent = '0';
        this.pairsTotal.textContent = '0';
        this.timerDisplay.textContent = '00:00';
        this.gameBoard.innerHTML = '';
        this.gameBoard.style.gridTemplateColumns = '';
        this.achievementsContainer.style.display = 'none';
        this.achievementsList.innerHTML = '';
        this.powerUpTray.innerHTML = '';
    }
    showModal(modalElement) { modalElement.classList.add('show'); }
    hideModal(modalElement) { modalElement.classList.remove('show'); }
    showNotification(message) {
        this.toastNotification.innerHTML = message;
        this.toastNotification.classList.add('show');
        setTimeout(() => {
            this.toastNotification.classList.remove('show');
        }, 3000);
    }
}
document.addEventListener('DOMContentLoaded', () => new MemoryGame());
