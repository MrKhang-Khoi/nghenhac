/**
 * player.js — Core Audio Player Engine
 * Vinyl Noir Music Player
 * 
 * Quản lý HTML5 Audio element, play/pause/seek/volume,
 * chế độ lặp, shuffle, và event dispatching.
 */

// Chế độ phát
export const PlayMode = {
    REPEAT_OFF: 'repeat-off',
    REPEAT_ONE: 'repeat-one',
    REPEAT_ALL: 'repeat-all',
    SHUFFLE: 'shuffle'
};

class AudioPlayer {
    constructor() {
        /** @type {HTMLAudioElement} */
        this.audio = new Audio();
        this.audio.preload = 'auto';
        this.audio.crossOrigin = 'anonymous';

        /** @type {Array} Danh sách bài hát */
        this.playlist = [];
        /** @type {number} Index bài đang phát */
        this.currentIndex = -1;
        /** @type {string} Chế độ phát hiện tại */
        this.playMode = PlayMode.REPEAT_ALL;
        /** @type {Array} Thứ tự shuffle */
        this.shuffleOrder = [];
        /** @type {number} Vị trí trong shuffle order */
        this.shufflePosition = -1;
        /** @type {boolean} Đang phát hay không */
        this.isPlaying = false;

        // Event callbacks — UI sẽ đăng ký
        this._callbacks = {
            onTrackChange: [],
            onPlayStateChange: [],
            onTimeUpdate: [],
            onError: [],
            onLoadStart: [],
            onCanPlay: [],
            onEnded: []
        };

        this._initAudioEvents();
    }

    /**
     * Khởi tạo event listeners cho audio element
     * @private
     */
    _initAudioEvents() {
        this.audio.addEventListener('timeupdate', () => {
            this._emit('onTimeUpdate', {
                currentTime: this.audio.currentTime,
                duration: this.audio.duration || 0,
                progress: this.audio.duration ? (this.audio.currentTime / this.audio.duration) : 0
            });
        });

        this.audio.addEventListener('ended', () => {
            this._handleTrackEnd();
        });

        this.audio.addEventListener('play', () => {
            this.isPlaying = true;
            this._emit('onPlayStateChange', { playing: true });
        });

        this.audio.addEventListener('pause', () => {
            this.isPlaying = false;
            this._emit('onPlayStateChange', { playing: false });
        });

        this.audio.addEventListener('loadstart', () => {
            this._emit('onLoadStart', {});
        });

        this.audio.addEventListener('canplay', () => {
            this._emit('onCanPlay', {
                duration: this.audio.duration
            });
        });

        this.audio.addEventListener('error', (event) => {
            const song = this.getCurrentSong();
            const errorMsg = this._getAudioErrorMessage(this.audio.error);
            console.error('[Player] Audio error:', errorMsg, song?.title);
            this._emit('onError', {
                message: errorMsg,
                song: song
            });
        });

        this.audio.addEventListener('waiting', () => {
            this._emit('onLoadStart', { buffering: true });
        });

        this.audio.addEventListener('playing', () => {
            this._emit('onCanPlay', { buffering: false });
        });
    }

    /**
     * Lấy thông báo lỗi audio dễ đọc
     * @private
     */
    _getAudioErrorMessage(error) {
        if (!error) return 'Lỗi không xác định';
        switch (error.code) {
            case MediaError.MEDIA_ERR_ABORTED:
                return 'Phát nhạc bị hủy';
            case MediaError.MEDIA_ERR_NETWORK:
                return 'Lỗi mạng khi tải nhạc';
            case MediaError.MEDIA_ERR_DECODE:
                return 'File nhạc bị lỗi hoặc không hỗ trợ';
            case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
                return 'Định dạng file không được hỗ trợ hoặc file không tồn tại';
            default:
                return 'Lỗi phát nhạc không xác định';
        }
    }

    /**
     * Đăng ký callback cho event
     * @param {string} eventName - Tên event
     * @param {Function} callback - Hàm callback
     */
    on(eventName, callback) {
        if (this._callbacks[eventName]) {
            this._callbacks[eventName].push(callback);
        }
    }

    /**
     * Hủy đăng ký callback
     * @param {string} eventName - Tên event
     * @param {Function} callback - Hàm callback cần hủy
     */
    off(eventName, callback) {
        if (this._callbacks[eventName]) {
            this._callbacks[eventName] = this._callbacks[eventName].filter(cb => cb !== callback);
        }
    }

    /**
     * Emit event đến tất cả callbacks đã đăng ký
     * @private
     */
    _emit(eventName, data) {
        if (this._callbacks[eventName]) {
            this._callbacks[eventName].forEach(cb => {
                try {
                    cb(data);
                } catch (err) {
                    console.error(`[Player] Callback error in ${eventName}:`, err);
                }
            });
        }
    }

    /**
     * Set playlist
     * @param {Array} songs - Mảng bài hát từ playlist.json
     */
    setPlaylist(songs) {
        this.playlist = songs || [];
        this._generateShuffleOrder();
    }

    /**
     * Lấy bài đang phát
     * @returns {Object|null} Bài hát hiện tại
     */
    getCurrentSong() {
        if (this.currentIndex >= 0 && this.currentIndex < this.playlist.length) {
            return this.playlist[this.currentIndex];
        }
        return null;
    }

    /**
     * Phát bài hát theo index
     * @param {number} index - Index trong playlist
     */
    async playByIndex(index) {
        if (index < 0 || index >= this.playlist.length) {
            console.error('[Player] Invalid index:', index);
            return;
        }

        this.currentIndex = index;
        const song = this.playlist[index];

        // Cập nhật shuffle position nếu đang ở chế độ shuffle
        if (this.playMode === PlayMode.SHUFFLE) {
            const shuffleIdx = this.shuffleOrder.indexOf(index);
            if (shuffleIdx !== -1) {
                this.shufflePosition = shuffleIdx;
            }
        }

        try {
            this.audio.src = song.audioUrl;
            await this.audio.play();
            this._emit('onTrackChange', { song, index });
        } catch (err) {
            console.error('[Player] Play failed:', err.message);
            // Nếu lỗi autoplay (blocked by browser), vẫn emit track change
            if (err.name === 'NotAllowedError') {
                this._emit('onTrackChange', { song, index });
                this._emit('onPlayStateChange', { playing: false });
            } else {
                this._emit('onError', { message: 'Không thể phát bài này', song });
            }
        }
    }

    /**
     * Phát bài hát theo ID
     * @param {string} songId - ID bài hát
     */
    async playById(songId) {
        const index = this.playlist.findIndex(s => s.id === songId);
        if (index !== -1) {
            await this.playByIndex(index);
        } else {
            console.error('[Player] Song not found:', songId);
        }
    }

    /**
     * Toggle play/pause
     */
    async toggle() {
        if (!this.audio.src) {
            // Chưa chọn bài, phát bài đầu tiên
            if (this.playlist.length > 0) {
                await this.playByIndex(0);
            }
            return;
        }

        if (this.isPlaying) {
            this.audio.pause();
        } else {
            try {
                await this.audio.play();
            } catch (err) {
                console.error('[Player] Resume failed:', err.message);
            }
        }
    }

    /** Pause */
    pause() {
        this.audio.pause();
    }

    /** Play (resume) */
    async play() {
        try {
            await this.audio.play();
        } catch (err) {
            console.error('[Player] Play failed:', err.message);
        }
    }

    /**
     * Chuyển bài tiếp theo
     */
    async next() {
        if (this.playlist.length === 0) return;

        let nextIndex;

        if (this.playMode === PlayMode.SHUFFLE) {
            this.shufflePosition = (this.shufflePosition + 1) % this.shuffleOrder.length;
            nextIndex = this.shuffleOrder[this.shufflePosition];
        } else {
            nextIndex = (this.currentIndex + 1) % this.playlist.length;
        }

        await this.playByIndex(nextIndex);
    }

    /**
     * Chuyển bài trước đó
     */
    async prev() {
        if (this.playlist.length === 0) return;

        // Nếu đang phát quá 3 giây, quay lại đầu bài
        if (this.audio.currentTime > 3) {
            this.audio.currentTime = 0;
            return;
        }

        let prevIndex;

        if (this.playMode === PlayMode.SHUFFLE) {
            this.shufflePosition = (this.shufflePosition - 1 + this.shuffleOrder.length) % this.shuffleOrder.length;
            prevIndex = this.shuffleOrder[this.shufflePosition];
        } else {
            prevIndex = (this.currentIndex - 1 + this.playlist.length) % this.playlist.length;
        }

        await this.playByIndex(prevIndex);
    }

    /**
     * Tua đến vị trí (0-1)
     * @param {number} fraction - Vị trí 0 đến 1
     */
    seek(fraction) {
        if (this.audio.duration && isFinite(this.audio.duration)) {
            this.audio.currentTime = fraction * this.audio.duration;
        }
    }

    /**
     * Tua đến thời gian cụ thể
     * @param {number} time - Thời gian (giây)
     */
    seekTo(time) {
        if (isFinite(time) && time >= 0) {
            this.audio.currentTime = Math.min(time, this.audio.duration || 0);
        }
    }

    /**
     * Set âm lượng
     * @param {number} volume - Âm lượng 0-1
     */
    setVolume(volume) {
        this.audio.volume = Math.max(0, Math.min(1, volume));
    }

    /** Lấy âm lượng hiện tại */
    getVolume() {
        return this.audio.volume;
    }

    /**
     * Đổi chế độ phát (cycle qua các mode)
     * @returns {string} Chế độ phát mới
     */
    cyclePlayMode() {
        const modes = [PlayMode.REPEAT_ALL, PlayMode.REPEAT_ONE, PlayMode.SHUFFLE, PlayMode.REPEAT_OFF];
        const currentIdx = modes.indexOf(this.playMode);
        this.playMode = modes[(currentIdx + 1) % modes.length];

        if (this.playMode === PlayMode.SHUFFLE) {
            this._generateShuffleOrder();
        }

        return this.playMode;
    }

    /**
     * Set chế độ phát cụ thể
     * @param {string} mode - Chế độ phát
     */
    setPlayMode(mode) {
        if (Object.values(PlayMode).includes(mode)) {
            this.playMode = mode;
            if (mode === PlayMode.SHUFFLE) {
                this._generateShuffleOrder();
            }
        }
    }

    /**
     * Xử lý khi bài hát kết thúc
     * @private
     */
    async _handleTrackEnd() {
        this._emit('onEnded', { song: this.getCurrentSong() });

        switch (this.playMode) {
            case PlayMode.REPEAT_ONE:
                this.audio.currentTime = 0;
                await this.play();
                break;

            case PlayMode.REPEAT_ALL:
                await this.next();
                break;

            case PlayMode.SHUFFLE:
                await this.next();
                break;

            case PlayMode.REPEAT_OFF:
                if (this.currentIndex < this.playlist.length - 1) {
                    await this.next();
                } else {
                    // Dừng ở bài cuối
                    this.isPlaying = false;
                    this._emit('onPlayStateChange', { playing: false });
                }
                break;
        }
    }

    /**
     * Tạo thứ tự shuffle (Fisher-Yates)
     * @private
     */
    _generateShuffleOrder() {
        this.shuffleOrder = Array.from({ length: this.playlist.length }, (_, i) => i);
        // Fisher-Yates shuffle
        for (let i = this.shuffleOrder.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.shuffleOrder[i], this.shuffleOrder[j]] = [this.shuffleOrder[j], this.shuffleOrder[i]];
        }

        // Đưa bài hiện tại lên đầu nếu đang phát
        if (this.currentIndex >= 0) {
            const currentPos = this.shuffleOrder.indexOf(this.currentIndex);
            if (currentPos > 0) {
                [this.shuffleOrder[0], this.shuffleOrder[currentPos]] = [this.shuffleOrder[currentPos], this.shuffleOrder[0]];
            }
            this.shufflePosition = 0;
        }
    }

    /**
     * Lấy thông tin thời gian hiện tại
     * @returns {{ currentTime: number, duration: number, progress: number }}
     */
    getTimeInfo() {
        return {
            currentTime: this.audio.currentTime || 0,
            duration: this.audio.duration || 0,
            progress: this.audio.duration ? (this.audio.currentTime / this.audio.duration) : 0
        };
    }

    /** Cleanup - giải phóng tài nguyên */
    destroy() {
        this.audio.pause();
        this.audio.src = '';
        this.audio.load();
        this._callbacks = {
            onTrackChange: [],
            onPlayStateChange: [],
            onTimeUpdate: [],
            onError: [],
            onLoadStart: [],
            onCanPlay: [],
            onEnded: []
        };
    }
}

// Singleton instance
const player = new AudioPlayer();
export default player;
