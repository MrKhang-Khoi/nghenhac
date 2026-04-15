/**
 * media-session.js — Media Session API Integration
 * Vinyl Noir Music Player
 * 
 * Hiện metadata bài hát trên lock screen Android,
 * điều khiển play/pause/next/prev từ notification & Bluetooth.
 */

import player from './player.js';

class MediaSessionManager {
    constructor() {
        this.supported = 'mediaSession' in navigator;
        if (!this.supported) {
            console.warn('[MediaSession] API không được hỗ trợ trên trình duyệt này');
        }
    }

    /**
     * Khởi tạo Media Session với player
     * Đăng ký action handlers cho lock screen controls
     */
    init() {
        if (!this.supported) return;

        // Đăng ký các action handlers
        const actionHandlers = {
            'play': () => player.play(),
            'pause': () => player.pause(),
            'previoustrack': () => player.prev(),
            'nexttrack': () => player.next(),
            'seekbackward': (details) => {
                const skipTime = details.seekOffset || 10;
                player.seekTo(Math.max(player.audio.currentTime - skipTime, 0));
                this._updatePositionState();
            },
            'seekforward': (details) => {
                const skipTime = details.seekOffset || 10;
                player.seekTo(Math.min(player.audio.currentTime + skipTime, player.audio.duration || 0));
                this._updatePositionState();
            },
            'seekto': (details) => {
                if (details.seekTime !== null && details.seekTime !== undefined) {
                    player.seekTo(details.seekTime);
                    this._updatePositionState();
                }
            }
        };

        for (const [action, handler] of Object.entries(actionHandlers)) {
            try {
                navigator.mediaSession.setActionHandler(action, handler);
            } catch (err) {
                console.warn(`[MediaSession] Action '${action}' không được hỗ trợ:`, err.message);
            }
        }

        // Lắng nghe track change từ player
        player.on('onTrackChange', ({ song }) => {
            this.updateMetadata(song);
        });

        // Lắng nghe time update để cập nhật position
        player.on('onTimeUpdate', () => {
            this._updatePositionState();
        });

        // Lắng nghe play state change
        player.on('onPlayStateChange', ({ playing }) => {
            if (this.supported) {
                navigator.mediaSession.playbackState = playing ? 'playing' : 'paused';
            }
        });

        console.log('[MediaSession] Đã khởi tạo thành công');
    }

    /**
     * Cập nhật metadata bài hát lên lock screen
     * @param {Object} song - Thông tin bài hát
     */
    updateMetadata(song) {
        if (!this.supported || !song) return;

        const coverUrl = song.cover || 'assets/covers/default-cover.jpg';

        try {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: song.title || 'Không rõ tên',
                artist: song.artist || 'Không rõ nghệ sĩ',
                album: song.album || '',
                artwork: [
                    { src: coverUrl, sizes: '96x96', type: 'image/jpeg' },
                    { src: coverUrl, sizes: '128x128', type: 'image/jpeg' },
                    { src: coverUrl, sizes: '192x192', type: 'image/jpeg' },
                    { src: coverUrl, sizes: '256x256', type: 'image/jpeg' },
                    { src: coverUrl, sizes: '384x384', type: 'image/jpeg' },
                    { src: coverUrl, sizes: '512x512', type: 'image/jpeg' }
                ]
            });
        } catch (err) {
            console.error('[MediaSession] Lỗi cập nhật metadata:', err);
        }
    }

    /**
     * Cập nhật position state (cho progress bar trên lock screen)
     * @private
     */
    _updatePositionState() {
        if (!this.supported) return;

        try {
            const duration = player.audio.duration;
            if (duration && isFinite(duration) && duration > 0) {
                navigator.mediaSession.setPositionState({
                    duration: duration,
                    playbackRate: player.audio.playbackRate || 1,
                    position: Math.min(player.audio.currentTime, duration)
                });
            }
        } catch (err) {
            // Bỏ qua lỗi position state (không critical)
        }
    }
}

const mediaSession = new MediaSessionManager();
export default mediaSession;
