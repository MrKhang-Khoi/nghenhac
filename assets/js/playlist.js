/**
 * playlist.js — Quản lý Playlist
 * Vinyl Noir Music Player
 * 
 * Fetch, parse, search, filter, và quản lý danh sách bài hát.
 */

class PlaylistManager {
    constructor() {
        /** @type {Array} Danh sách bài hát gốc */
        this.songs = [];
        /** @type {Array} Danh sách bài hát đã lọc (search result) */
        this.filteredSongs = [];
        /** @type {Set} Danh sách ID bài yêu thích (lưu localStorage) */
        this.favorites = new Set();
        /** @type {boolean} Đã load thành công chưa */
        this.loaded = false;

        this._loadFavorites();
    }

    /**
     * Fetch danh sách bài hát từ playlist.json
     * @param {string} url - Đường dẫn playlist.json
     * @returns {Promise<Array>} Mảng bài hát
     */
    async loadPlaylist(url = 'data/playlist.json') {
        try {
            const cacheBuster = `?t=${Date.now()}`;
            const response = await fetch(url + cacheBuster);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            if (!Array.isArray(data)) {
                throw new Error('playlist.json không phải mảng hợp lệ');
            }

            // Validate và normalize từng bài
            this.songs = data.map((song, index) => this._normalizeSong(song, index));
            this.filteredSongs = [...this.songs];

            // Merge trạng thái favorite từ localStorage
            this.songs.forEach(song => {
                song.favorite = this.favorites.has(song.id);
            });

            this.loaded = true;
            console.log(`[Playlist] Đã tải ${this.songs.length} bài hát`);
            return this.songs;

        } catch (err) {
            console.error('[Playlist] Lỗi tải playlist:', err.message);
            this.songs = [];
            this.filteredSongs = [];
            throw err;
        }
    }

    /**
     * Normalize dữ liệu bài hát — đảm bảo schema đúng
     * @private
     */
    _normalizeSong(song, index) {
        return {
            id: song.id || `song-${index}`,
            title: song.title || `Bài hát ${index + 1}`,
            artist: song.artist || 'Không rõ',
            album: song.album || '',
            cover: song.cover || 'assets/covers/default-cover.jpg',
            audioUrl: song.audioUrl || '',
            duration: song.duration || 0,
            lyrics: song.lyrics || '',
            favorite: song.favorite || false
        };
    }

    /**
     * Tìm kiếm bài hát theo từ khóa
     * @param {string} query - Từ khóa tìm kiếm
     * @returns {Array} Kết quả tìm kiếm
     */
    search(query) {
        if (!query || query.trim() === '') {
            this.filteredSongs = [...this.songs];
            return this.filteredSongs;
        }

        const normalizedQuery = this._normalizeText(query);

        this.filteredSongs = this.songs.filter(song => {
            const titleMatch = this._normalizeText(song.title).includes(normalizedQuery);
            const artistMatch = this._normalizeText(song.artist).includes(normalizedQuery);
            const albumMatch = this._normalizeText(song.album).includes(normalizedQuery);
            return titleMatch || artistMatch || albumMatch;
        });

        return this.filteredSongs;
    }

    /**
     * Normalize text cho tìm kiếm (bỏ dấu, lowercase)
     * @private
     */
    _normalizeText(text) {
        return text
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/đ/g, 'd')
            .replace(/Đ/g, 'D');
    }

    /**
     * Toggle yêu thích cho bài hát
     * @param {string} songId - ID bài hát
     * @returns {boolean} Trạng thái favorite mới
     */
    toggleFavorite(songId) {
        const song = this.songs.find(s => s.id === songId);
        if (!song) return false;

        if (this.favorites.has(songId)) {
            this.favorites.delete(songId);
            song.favorite = false;
        } else {
            this.favorites.add(songId);
            song.favorite = true;
        }

        this._saveFavorites();
        return song.favorite;
    }

    /**
     * Lấy danh sách bài yêu thích
     * @returns {Array} Bài yêu thích
     */
    getFavorites() {
        return this.songs.filter(s => this.favorites.has(s.id));
    }

    /**
     * Lấy bài hát theo ID
     * @param {string} songId - ID bài hát
     * @returns {Object|null}
     */
    getSongById(songId) {
        return this.songs.find(s => s.id === songId) || null;
    }

    /**
     * Lấy index của bài hát theo ID
     * @param {string} songId
     * @returns {number} Index hoặc -1
     */
    getIndexById(songId) {
        return this.songs.findIndex(s => s.id === songId);
    }

    /**
     * Lưu danh sách yêu thích vào localStorage
     * @private
     */
    _saveFavorites() {
        try {
            localStorage.setItem('vinyl-noir-favorites', JSON.stringify([...this.favorites]));
        } catch (err) {
            console.error('[Playlist] Lỗi lưu favorites:', err);
        }
    }

    /**
     * Load danh sách yêu thích từ localStorage
     * @private
     */
    _loadFavorites() {
        try {
            const saved = localStorage.getItem('vinyl-noir-favorites');
            if (saved) {
                this.favorites = new Set(JSON.parse(saved));
            }
        } catch (err) {
            console.error('[Playlist] Lỗi đọc favorites:', err);
            this.favorites = new Set();
        }
    }
}

const playlistManager = new PlaylistManager();
export default playlistManager;
