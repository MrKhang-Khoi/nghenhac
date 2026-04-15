/**
 * ui.js — DOM Manipulation & Animations
 * Vinyl Noir Music Player
 * 
 * Render giao diện, xử lý tương tác, cập nhật trạng thái visual.
 */

import player, { PlayMode } from './player.js';
import playlistManager from './playlist.js';
import storageManager from './storage.js';
import { formatTime, debounce, formatBytes } from './utils.js';

class UIManager {
    constructor() {
        this.elements = {};
        this.currentView = 'now-playing'; // 'now-playing' hoặc 'playlist'
        this.isProgressDragging = false;
        this.toastTimeout = null;
    }

    /**
     * Khởi tạo UI — lấy references đến DOM elements
     */
    init() {
        // Cache tất cả DOM elements
        this.elements = {
            // Views
            nowPlaying: document.getElementById('now-playing'),
            playlistView: document.getElementById('playlist-view'),

            // Vinyl player
            vinylDisc: document.getElementById('vinyl-disc'),
            vinylCover: document.getElementById('vinyl-cover'),
            trackTitle: document.getElementById('track-title'),
            trackArtist: document.getElementById('track-artist'),

            // Progress
            progressWrapper: document.getElementById('progress-wrapper'),
            progressFill: document.getElementById('progress-fill'),
            currentTime: document.getElementById('current-time'),
            totalTime: document.getElementById('total-time'),

            // Controls
            prevBtn: document.getElementById('btn-prev'),
            playBtn: document.getElementById('btn-play'),
            nextBtn: document.getElementById('btn-next'),
            modeBtn: document.getElementById('btn-mode'),
            favoriteBtn: document.getElementById('btn-favorite'),
            volumeSlider: document.getElementById('volume-slider'),
            volumeIcon: document.getElementById('volume-icon'),

            // Mini player
            miniPlayer: document.getElementById('mini-player'),
            miniCover: document.getElementById('mini-cover'),
            miniTitle: document.getElementById('mini-title'),
            miniArtist: document.getElementById('mini-artist'),
            miniPlayBtn: document.getElementById('mini-play'),
            miniNextBtn: document.getElementById('mini-next'),
            miniProgressFill: document.getElementById('mini-progress-fill'),

            // Playlist
            songList: document.getElementById('song-list'),
            searchInput: document.getElementById('search-input'),
            searchClear: document.getElementById('search-clear'),
            songCount: document.getElementById('song-count'),

            // Navigation
            navTabs: document.getElementById('nav-tabs'),
            tabNowPlaying: document.getElementById('tab-now-playing'),
            tabPlaylist: document.getElementById('tab-playlist'),

            // Settings
            settingsPanel: document.getElementById('settings-panel'),
            settingsBtn: document.getElementById('btn-settings'),
            settingsClose: document.getElementById('settings-close'),
            cacheSize: document.getElementById('cache-size'),
            btnDownloadAll: document.getElementById('btn-download-all'),
            btnClearCache: document.getElementById('btn-clear-cache'),

            // Status
            statusBanner: document.getElementById('status-banner'),
            toast: document.getElementById('toast'),
        };

        this._bindEvents();
        this._bindPlayerEvents();
        this._updateModeButton();

        // Set initial volume
        const savedVolume = localStorage.getItem('vinyl-noir-volume');
        if (savedVolume !== null) {
            player.setVolume(parseFloat(savedVolume));
            this.elements.volumeSlider.value = savedVolume;
        }

        console.log('[UI] Đã khởi tạo giao diện');
    }

    /**
     * Bind UI event listeners
     * @private
     */
    _bindEvents() {
        const el = this.elements;

        // Play/Pause
        el.playBtn.addEventListener('click', () => player.toggle());
        el.miniPlayBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            player.toggle();
        });

        // Prev/Next
        el.prevBtn.addEventListener('click', () => player.prev());
        el.nextBtn.addEventListener('click', () => player.next());
        el.miniNextBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            player.next();
        });

        // Play mode
        el.modeBtn.addEventListener('click', () => {
            player.cyclePlayMode();
            this._updateModeButton();
        });

        // Favorite
        el.favoriteBtn.addEventListener('click', () => {
            const song = player.getCurrentSong();
            if (song) {
                const isFav = playlistManager.toggleFavorite(song.id);
                this._updateFavoriteButton(isFav);
                this.showToast(isFav ? '❤️ Đã thêm vào yêu thích' : '💔 Đã bỏ yêu thích');
                this.renderSongList(playlistManager.filteredSongs);
            }
        });

        // Progress bar interaction (mouse + touch)
        el.progressWrapper.addEventListener('pointerdown', (e) => {
            this.isProgressDragging = true;
            this._seekFromPointerEvent(e);
            el.progressWrapper.setPointerCapture(e.pointerId);
        });

        el.progressWrapper.addEventListener('pointermove', (e) => {
            if (this.isProgressDragging) {
                this._seekFromPointerEvent(e);
            }
        });

        el.progressWrapper.addEventListener('pointerup', () => {
            this.isProgressDragging = false;
        });

        // Volume
        el.volumeSlider.addEventListener('input', (e) => {
            const volume = parseFloat(e.target.value);
            player.setVolume(volume);
            localStorage.setItem('vinyl-noir-volume', volume);
            this._updateVolumeIcon(volume);
        });

        // Search
        el.searchInput.addEventListener('input', debounce((e) => {
            const query = e.target.value;
            el.searchClear.classList.toggle('visible', query.length > 0);
            const results = playlistManager.search(query);
            this.renderSongList(results);
        }, 200));

        el.searchClear.addEventListener('click', () => {
            el.searchInput.value = '';
            el.searchClear.classList.remove('visible');
            playlistManager.search('');
            this.renderSongList(playlistManager.songs);
        });

        // Navigation tabs
        el.tabNowPlaying.addEventListener('click', () => this.switchView('now-playing'));
        el.tabPlaylist.addEventListener('click', () => this.switchView('playlist'));

        // Mini player — tap to switch to now playing
        el.miniPlayer.querySelector('.mini-player-content').addEventListener('click', () => {
            this.switchView('now-playing');
        });

        // Settings
        el.settingsBtn.addEventListener('click', () => this.openSettings());
        el.settingsClose.addEventListener('click', () => this.closeSettings());
        el.settingsPanel.addEventListener('click', (e) => {
            if (e.target === el.settingsPanel) this.closeSettings();
        });

        // Cache actions
        el.btnDownloadAll.addEventListener('click', () => this._downloadAllForOffline());
        el.btnClearCache.addEventListener('click', () => this._clearAllCache());

        // Online/Offline detection
        window.addEventListener('online', () => this._showNetworkStatus(true));
        window.addEventListener('offline', () => this._showNetworkStatus(false));
    }

    /**
     * Bind player event callbacks
     * @private
     */
    _bindPlayerEvents() {
        player.on('onTrackChange', ({ song, index }) => {
            this._updateNowPlaying(song);
            this._updateMiniPlayer(song);
            this._highlightActiveSong(song.id);
            this._updateFavoriteButton(playlistManager.favorites.has(song.id));
        });

        player.on('onPlayStateChange', ({ playing }) => {
            this._updatePlayButtons(playing);
            this._updateVinylSpin(playing);
        });

        player.on('onTimeUpdate', ({ currentTime, duration, progress }) => {
            if (!this.isProgressDragging) {
                this.elements.progressFill.style.width = `${progress * 100}%`;
                this.elements.miniProgressFill.style.width = `${progress * 100}%`;
                this.elements.currentTime.textContent = formatTime(currentTime);
                this.elements.totalTime.textContent = formatTime(duration);
            }
        });

        player.on('onError', ({ message, song }) => {
            this.showToast(`⚠️ ${message}`, 'error');
        });

        player.on('onLoadStart', () => {
            this.elements.playBtn.classList.add('loading');
        });

        player.on('onCanPlay', () => {
            this.elements.playBtn.classList.remove('loading');
        });
    }

    /**
     * Seek theo pointer event position
     * @private
     */
    _seekFromPointerEvent(event) {
        const rect = this.elements.progressWrapper.getBoundingClientRect();
        const fraction = Math.max(0, Math.min(1, (event.clientX - rect.left) / rect.width));
        player.seek(fraction);
        this.elements.progressFill.style.width = `${fraction * 100}%`;
    }

    /**
     * Cập nhật giao diện Now Playing
     * @private
     */
    _updateNowPlaying(song) {
        this.elements.trackTitle.textContent = song.title;
        this.elements.trackArtist.textContent = song.artist;
        this.elements.vinylCover.src = song.cover || 'assets/covers/default-cover.jpg';
        this.elements.vinylCover.alt = song.title;

        // Reset progress
        this.elements.progressFill.style.width = '0%';
        this.elements.currentTime.textContent = '0:00';
        this.elements.totalTime.textContent = formatTime(song.duration);
    }

    /**
     * Cập nhật mini player
     * @private
     */
    _updateMiniPlayer(song) {
        const el = this.elements;
        el.miniPlayer.classList.add('visible');
        el.navTabs.classList.remove('no-mini-player');
        el.miniCover.src = song.cover || 'assets/covers/default-cover.jpg';
        el.miniTitle.textContent = song.title;
        el.miniArtist.textContent = song.artist;
    }

    /**
     * Cập nhật trạng thái nút play/pause
     * @private
     */
    _updatePlayButtons(playing) {
        const playIcon = playing ? '⏸' : '▶';
        this.elements.playBtn.textContent = playIcon;
        this.elements.miniPlayBtn.textContent = playIcon;
    }

    /**
     * Bật/tắt quay đĩa vinyl
     * @private
     */
    _updateVinylSpin(playing) {
        this.elements.vinylDisc.classList.toggle('spinning', playing);
    }

    /**
     * Cập nhật nút chế độ phát
     * @private
     */
    _updateModeButton() {
        const icons = {
            [PlayMode.REPEAT_ALL]: '🔁',
            [PlayMode.REPEAT_ONE]: '🔂',
            [PlayMode.SHUFFLE]: '🔀',
            [PlayMode.REPEAT_OFF]: '➡️'
        };
        this.elements.modeBtn.textContent = icons[player.playMode] || '🔁';
        this.elements.modeBtn.classList.toggle('active', player.playMode !== PlayMode.REPEAT_OFF);
    }

    /**
     * Cập nhật nút yêu thích
     * @private
     */
    _updateFavoriteButton(isFavorite) {
        this.elements.favoriteBtn.textContent = isFavorite ? '❤️' : '🤍';
        this.elements.favoriteBtn.classList.toggle('active', isFavorite);
    }

    /**
     * Cập nhật icon volume
     * @private
     */
    _updateVolumeIcon(volume) {
        if (volume === 0) {
            this.elements.volumeIcon.textContent = '🔇';
        } else if (volume < 0.5) {
            this.elements.volumeIcon.textContent = '🔉';
        } else {
            this.elements.volumeIcon.textContent = '🔊';
        }
    }

    /**
     * Render danh sách bài hát
     * @param {Array} songs - Mảng bài hát cần render
     */
    async renderSongList(songs) {
        const container = this.elements.songList;

        // Update song count
        this.elements.songCount.textContent = `${songs.length} bài hát`;

        if (songs.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🎵</div>
                    <div class="empty-state-text">Không tìm thấy bài hát nào</div>
                </div>
            `;
            return;
        }

        // Build HTML
        const currentSong = player.getCurrentSong();
        let html = '';

        for (let i = 0; i < songs.length; i++) {
            const song = songs[i];
            const isPlaying = currentSong && currentSong.id === song.id;
            const isFav = playlistManager.favorites.has(song.id);
            const isOffline = await storageManager.isAvailableOffline(song.audioUrl);

            html += `
                <div class="song-card ${isPlaying ? 'playing' : ''}" 
                     data-id="${song.id}" 
                     data-index="${i}"
                     style="animation-delay: ${Math.min(i * 40, 600)}ms">
                    <img class="song-card-cover" 
                         src="${song.cover || 'assets/covers/default-cover.jpg'}" 
                         alt="${song.title}"
                         loading="lazy"
                         onerror="this.src='assets/covers/default-cover.jpg'">
                    <div class="song-card-info">
                        <div class="song-card-title">${song.title}</div>
                        <div class="song-card-artist">${song.artist}</div>
                    </div>
                    <div class="song-card-actions">
                        ${isOffline ? '<span class="offline-badge" title="Có sẵn offline">✅</span>' : ''}
                        <span class="song-card-duration">${song.duration ? formatTime(song.duration) : ''}</span>
                        <button class="favorite-btn ${isFav ? 'active' : ''}" 
                                data-song-id="${song.id}"
                                title="${isFav ? 'Bỏ yêu thích' : 'Thêm yêu thích'}">
                            ${isFav ? '❤️' : '🤍'}
                        </button>
                    </div>
                </div>
            `;
        }

        container.innerHTML = html;

        // Bind click events cho song cards
        container.querySelectorAll('.song-card').forEach(card => {
            card.addEventListener('click', (e) => {
                // Bỏ qua nếu click vào nút favorite
                if (e.target.closest('.favorite-btn')) return;

                const songId = card.dataset.id;
                const index = playlistManager.songs.findIndex(s => s.id === songId);
                if (index !== -1) {
                    player.playByIndex(index);
                    // Mobile: tự chuyển sang now playing
                    if (window.innerWidth < 768) {
                        this.switchView('now-playing');
                    }
                }
            });
        });

        // Bind favorite buttons
        container.querySelectorAll('.favorite-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const songId = btn.dataset.songId;
                const isFav = playlistManager.toggleFavorite(songId);
                btn.textContent = isFav ? '❤️' : '🤍';
                btn.classList.toggle('active', isFav);

                // Cập nhật main favorite button nếu đang phát bài này
                const currentSong = player.getCurrentSong();
                if (currentSong && currentSong.id === songId) {
                    this._updateFavoriteButton(isFav);
                }
            });
        });
    }

    /**
     * Highlight bài đang phát trong danh sách
     * @private
     */
    _highlightActiveSong(songId) {
        this.elements.songList.querySelectorAll('.song-card').forEach(card => {
            card.classList.toggle('playing', card.dataset.id === songId);
        });
    }

    /**
     * Chuyển đổi view (now-playing / playlist)
     * @param {string} view - 'now-playing' hoặc 'playlist'
     */
    switchView(view) {
        this.currentView = view;

        const isNowPlaying = view === 'now-playing';
        this.elements.nowPlaying.classList.toggle('hidden', !isNowPlaying);
        this.elements.playlistView.classList.toggle('hidden', isNowPlaying);

        this.elements.tabNowPlaying.classList.toggle('active', isNowPlaying);
        this.elements.tabPlaylist.classList.toggle('active', !isNowPlaying);
    }

    /**
     * Mở settings panel
     */
    async openSettings() {
        this.elements.settingsPanel.classList.add('visible');
        const cacheInfo = await storageManager.getCacheSize();
        this.elements.cacheSize.textContent = cacheInfo.formatted || '0 B';
    }

    /** Đóng settings panel */
    closeSettings() {
        this.elements.settingsPanel.classList.remove('visible');
    }

    /**
     * Hiện toast message
     * @param {string} message - Nội dung
     * @param {string} type - 'default' | 'error' | 'success'
     */
    showToast(message, type = 'default') {
        const toast = this.elements.toast;
        toast.textContent = message;
        toast.className = `toast visible ${type}`;

        clearTimeout(this.toastTimeout);
        this.toastTimeout = setTimeout(() => {
            toast.classList.remove('visible');
        }, 2500);
    }

    /**
     * Hiện trạng thái online/offline
     * @private
     */
    _showNetworkStatus(isOnline) {
        const banner = this.elements.statusBanner;
        banner.textContent = isOnline ? '✅ Đã kết nối mạng' : '📴 Không có kết nối mạng';
        banner.className = `status-banner visible ${isOnline ? 'online' : 'offline'}`;

        if (isOnline) {
            setTimeout(() => {
                banner.classList.remove('visible');
            }, 2000);
        }
    }

    /**
     * Tải toàn bộ playlist offline
     * @private
     */
    async _downloadAllForOffline() {
        if (playlistManager.songs.length === 0) {
            this.showToast('⚠️ Không có bài hát nào', 'error');
            return;
        }

        this.showToast('⬇️ Đang tải tất cả bài hát...');

        const result = await storageManager.downloadAll(playlistManager.songs, (i, total, status, song) => {
            this.elements.btnDownloadAll.textContent = `⬇️ Đang tải ${i + 1}/${total}...`;
        });

        this.elements.btnDownloadAll.textContent = '⬇️ Tải tất cả để nghe offline';
        this.showToast(`✅ Đã tải ${result.successful}/${result.total} bài`, 'success');

        // Refresh cache size + song list
        const cacheInfo = await storageManager.getCacheSize();
        this.elements.cacheSize.textContent = cacheInfo.formatted;
        this.renderSongList(playlistManager.filteredSongs);
    }

    /**
     * Xóa toàn bộ cache
     * @private
     */
    async _clearAllCache() {
        if (!confirm('Bạn có chắc muốn xóa toàn bộ dữ liệu offline?')) return;

        await storageManager.clearAllCache();
        this.elements.cacheSize.textContent = '0 B';
        this.showToast('🗑️ Đã xóa toàn bộ cache', 'success');
        this.renderSongList(playlistManager.filteredSongs);
    }
}

const ui = new UIManager();
export default ui;
