/**
 * app.js — Main Application Entry Point
 * Vinyl Noir Music Player
 * 
 * Khởi tạo tất cả modules, load playlist, register service worker.
 */

import player from './player.js';
import playlistManager from './playlist.js';
import mediaSession from './media-session.js';
import ui from './ui.js';
import storageManager from './storage.js';

class VinylNoirApp {
    constructor() {
        this.initialized = false;
    }

    /**
     * Khởi tạo toàn bộ ứng dụng
     */
    async init() {
        if (this.initialized) return;

        try {
            console.log('[App] 🎵 Vinyl Noir — Đang khởi tạo...');

            // 1. Register Service Worker
            await this._registerServiceWorker();

            // 2. Init UI
            ui.init();

            // 3. Load playlist
            await this._loadPlaylist();

            // 4. Init Media Session
            mediaSession.init();

            // 5. Restore last state
            this._restoreState();

            this.initialized = true;
            console.log('[App] ✅ Khởi tạo hoàn tất!');

        } catch (err) {
            console.error('[App] ❌ Lỗi khởi tạo:', err);
            ui.showToast('⚠️ Lỗi khởi tạo ứng dụng', 'error');
        }
    }

    /**
     * Đăng ký Service Worker
     * @private
     */
    async _registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('./service-worker.js');
                console.log('[App] Service Worker đã đăng ký:', registration.scope);

                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'activated') {
                            ui.showToast('🔄 Ứng dụng đã cập nhật! Tải lại để dùng bản mới.', 'success');
                        }
                    });
                });
            } catch (err) {
                console.warn('[App] Service Worker lỗi:', err.message);
            }
        }
    }

    /**
     * Load playlist từ JSON
     * @private
     */
    async _loadPlaylist() {
        try {
            const songs = await playlistManager.loadPlaylist();
            player.setPlaylist(songs);
            ui.renderSongList(songs);

            if (songs.length === 0) {
                ui.showToast('📋 Chưa có bài hát. Dùng Music Manager để thêm nhạc!');
            }
        } catch (err) {
            console.error('[App] Lỗi tải playlist:', err);
            ui.showToast('⚠️ Không tải được danh sách nhạc', 'error');
        }
    }

    /**
     * Restore trạng thái trước đó (volume, play mode)
     * @private
     */
    _restoreState() {
        try {
            // Restore play mode
            const savedMode = localStorage.getItem('vinyl-noir-play-mode');
            if (savedMode) {
                player.setPlayMode(savedMode);
            }

            // Save play mode khi thay đổi
            player.on('onPlayStateChange', () => {
                localStorage.setItem('vinyl-noir-play-mode', player.playMode);
            });

        } catch (err) {
            console.warn('[App] Không restore được state:', err.message);
        }
    }
}

// Boot app khi DOM ready
const app = new VinylNoirApp();

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => app.init());
} else {
    app.init();
}

export default app;
