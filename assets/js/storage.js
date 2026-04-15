/**
 * storage.js — Cache Management & Offline Support
 * Vinyl Noir Music Player
 * 
 * Quản lý Cache API cho tải offline, theo dõi dung lượng,
 * và kiểm tra trạng thái offline từng bài.
 */

import { formatBytes } from './utils.js';

const AUDIO_CACHE_NAME = 'vinyl-noir-audio-v3';
const COVER_CACHE_NAME = 'vinyl-noir-covers-v3';

class StorageManager {
    constructor() {
        this.supported = 'caches' in window;
        if (!this.supported) {
            console.warn('[Storage] Cache API không được hỗ trợ');
        }
    }

    /**
     * Tải bài hát để nghe offline
     * @param {Object} song - Thông tin bài hát
     * @param {Function} onProgress - Callback progress (0-1)
     * @returns {Promise<boolean>} Thành công hay không
     */
    async downloadForOffline(song, onProgress = null) {
        if (!this.supported) return false;

        try {
            // Tải audio
            const audioCache = await caches.open(AUDIO_CACHE_NAME);
            const audioResponse = await this._fetchWithProgress(song.audioUrl, onProgress);
            
            if (!audioResponse || !audioResponse.ok) {
                throw new Error('Không tải được file nhạc');
            }
            await audioCache.put(song.audioUrl, audioResponse);

            // Tải cover nếu có
            if (song.cover) {
                try {
                    const coverCache = await caches.open(COVER_CACHE_NAME);
                    const coverResponse = await fetch(song.cover);
                    if (coverResponse.ok) {
                        await coverCache.put(song.cover, coverResponse);
                    }
                } catch (err) {
                    // Cover không tải được không critical
                    console.warn('[Storage] Không tải được cover:', err.message);
                }
            }

            console.log(`[Storage] Đã cache offline: ${song.title}`);
            return true;

        } catch (err) {
            console.error(`[Storage] Lỗi cache ${song.title}:`, err.message);
            return false;
        }
    }

    /**
     * Fetch với theo dõi progress
     * @private
     */
    async _fetchWithProgress(url, onProgress) {
        const response = await fetch(url);
        if (!onProgress) return response;

        const reader = response.body?.getReader();
        if (!reader) return response;

        const contentLength = parseInt(response.headers.get('content-length') || '0', 10);
        let receivedLength = 0;
        const chunks = [];

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            chunks.push(value);
            receivedLength += value.length;
            if (contentLength > 0) {
                onProgress(receivedLength / contentLength);
            }
        }

        const blob = new Blob(chunks);
        return new Response(blob, {
            status: response.status,
            statusText: response.statusText,
            headers: response.headers
        });
    }

    /**
     * Tải toàn bộ playlist để nghe offline
     * @param {Array} songs - Danh sách bài hát
     * @param {Function} onItemProgress - Callback cho mỗi bài (index, total, status)
     */
    async downloadAll(songs, onItemProgress = null) {
        let successful = 0;
        let failed = 0;

        for (let i = 0; i < songs.length; i++) {
            const song = songs[i];
            const alreadyCached = await this.isAvailableOffline(song.audioUrl);
            
            if (alreadyCached) {
                successful++;
                if (onItemProgress) onItemProgress(i, songs.length, 'skipped', song);
                continue;
            }

            const success = await this.downloadForOffline(song);
            if (success) {
                successful++;
                if (onItemProgress) onItemProgress(i, songs.length, 'success', song);
            } else {
                failed++;
                if (onItemProgress) onItemProgress(i, songs.length, 'failed', song);
            }
        }

        return { successful, failed, total: songs.length };
    }

    /**
     * Kiểm tra bài hát đã cache offline chưa
     * @param {string} audioUrl - URL file audio
     * @returns {Promise<boolean>}
     */
    async isAvailableOffline(audioUrl) {
        if (!this.supported) return false;

        try {
            const cache = await caches.open(AUDIO_CACHE_NAME);
            const response = await cache.match(audioUrl);
            return !!response;
        } catch {
            return false;
        }
    }

    /**
     * Xóa cache 1 bài
     * @param {Object} song - Bài hát cần xóa cache
     */
    async removeFromCache(song) {
        if (!this.supported) return;

        try {
            const audioCache = await caches.open(AUDIO_CACHE_NAME);
            await audioCache.delete(song.audioUrl);

            if (song.cover) {
                const coverCache = await caches.open(COVER_CACHE_NAME);
                await coverCache.delete(song.cover);
            }

            console.log(`[Storage] Đã xóa cache: ${song.title}`);
        } catch (err) {
            console.error('[Storage] Lỗi xóa cache:', err.message);
        }
    }

    /**
     * Xóa toàn bộ cache audio
     */
    async clearAllCache() {
        if (!this.supported) return;

        try {
            await caches.delete(AUDIO_CACHE_NAME);
            await caches.delete(COVER_CACHE_NAME);
            console.log('[Storage] Đã xóa toàn bộ cache');
        } catch (err) {
            console.error('[Storage] Lỗi xóa cache:', err.message);
        }
    }

    /**
     * Tính tổng dung lượng cache
     * @returns {Promise<{bytes: number, formatted: string}>}
     */
    async getCacheSize() {
        if (!this.supported) return { bytes: 0, formatted: '0 B' };

        try {
            // Thử dùng Storage Manager API (chính xác hơn)
            if ('storage' in navigator && 'estimate' in navigator.storage) {
                const estimate = await navigator.storage.estimate();
                return {
                    bytes: estimate.usage || 0,
                    formatted: formatBytes(estimate.usage || 0),
                    quota: estimate.quota || 0,
                    quotaFormatted: formatBytes(estimate.quota || 0)
                };
            }

            // Fallback: ước lượng từ cache entries
            let totalSize = 0;

            for (const cacheName of [AUDIO_CACHE_NAME, COVER_CACHE_NAME]) {
                try {
                    const cache = await caches.open(cacheName);
                    const keys = await cache.keys();
                    for (const request of keys) {
                        const response = await cache.match(request);
                        if (response) {
                            const blob = await response.blob();
                            totalSize += blob.size;
                        }
                    }
                } catch {
                    // Cache might not exist yet
                }
            }

            return {
                bytes: totalSize,
                formatted: formatBytes(totalSize)
            };
        } catch (err) {
            console.error('[Storage] Lỗi tính dung lượng:', err);
            return { bytes: 0, formatted: '0 B' };
        }
    }

    /**
     * Lấy danh sách các bài đã cache
     * @returns {Promise<Array<string>>} URLs đã cache
     */
    async getCachedUrls() {
        if (!this.supported) return [];

        try {
            const cache = await caches.open(AUDIO_CACHE_NAME);
            const keys = await cache.keys();
            return keys.map(req => req.url);
        } catch {
            return [];
        }
    }
}

const storageManager = new StorageManager();
export default storageManager;
