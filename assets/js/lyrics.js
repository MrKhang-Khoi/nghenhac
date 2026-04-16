/**
 * lyrics.js — Lyrics Display & Sync Engine
 * Vinyl Noir Music Player
 * 
 * Parse LRC format, đồng bộ với audio,
 * auto-scroll, highlight dòng đang hát.
 */

import player from './player.js';

class LyricsManager {
    constructor() {
        /** @type {Array<{time: number, text: string}>} */
        this.syncedLines = [];
        /** @type {string} */
        this.plainText = '';
        /** @type {number} */
        this.activeLine = -1;
        /** @type {boolean} */
        this.isVisible = false;
        /** @type {boolean} */
        this.hasLyrics = false;

        this._elements = {};
    }

    /**
     * Khởi tạo — gọi sau khi DOM sẵn sàng
     */
    init() {
        this._elements = {
            panel: document.getElementById('lyrics-panel'),
            container: document.getElementById('lyrics-container'),
            toggleBtn: document.getElementById('btn-lyrics'),
            vinylContainer: document.querySelector('.vinyl-container'),
        };

        // Toggle button
        if (this._elements.toggleBtn) {
            this._elements.toggleBtn.addEventListener('click', () => this.toggle());
        }

        // Sync lyrics với thời gian phát
        player.on('onTimeUpdate', ({ currentTime }) => {
            if (this.isVisible && this.syncedLines.length > 0) {
                this._syncToTime(currentTime);
            }
        });

        // Load lyrics khi đổi bài
        player.on('onTrackChange', ({ song }) => {
            this.loadForSong(song);
        });

        console.log('[Lyrics] Đã khởi tạo module lời bài hát');
    }

    /**
     * Load lyrics cho bài hát
     * @param {Object} song - Bài hát từ playlist
     */
    loadForSong(song) {
        this.activeLine = -1;
        const lyricsText = song?.lyrics || '';

        if (!lyricsText) {
            this.syncedLines = [];
            this.plainText = '';
            this.hasLyrics = false;
            this._render();
            this._updateToggleIndicator();
            return;
        }

        // Thử parse LRC format
        const parsed = this._parseLRC(lyricsText);

        if (parsed.length > 0) {
            this.syncedLines = parsed;
            this.plainText = '';
        } else {
            // Fallback: plain text
            this.syncedLines = [];
            this.plainText = lyricsText;
        }

        this.hasLyrics = true;
        this._render();
        this._updateToggleIndicator();
    }

    /**
     * Cập nhật indicator trên nút toggle
     * @private
     */
    _updateToggleIndicator() {
        const btn = this._elements.toggleBtn;
        if (!btn) return;
        btn.classList.toggle('has-lyrics', this.hasLyrics);
    }

    /**
     * Parse LRC format → array of {time, text}
     * Hỗ trợ: [mm:ss.xx], [mm:ss.xxx], [mm:ss]
     * @private
     */
    _parseLRC(text) {
        const lines = [];
        for (const line of text.split('\n')) {
            // Match: [mm:ss.xx] hoặc [mm:ss.xxx] hoặc [mm:ss]
            const match = line.match(/\[(\d{1,2}):(\d{2})(?:\.(\d{2,3}))?\]\s*(.*)/);
            if (match) {
                const mins = parseInt(match[1]);
                const secs = parseInt(match[2]);
                const msRaw = match[3] ? parseInt(match[3]) : 0;
                const ms = match[3] && match[3].length === 2 ? msRaw / 100 : msRaw / 1000;
                const time = mins * 60 + secs + ms;
                const content = match[4].trim();
                if (content) {
                    lines.push({ time, text: content });
                }
            }
        }
        return lines.sort((a, b) => a.time - b.time);
    }

    /**
     * Đồng bộ highlight với thời gian hiện tại
     * @private
     */
    _syncToTime(currentTime) {
        let newActive = -1;
        for (let i = this.syncedLines.length - 1; i >= 0; i--) {
            if (currentTime >= this.syncedLines[i].time - 0.15) {
                newActive = i;
                break;
            }
        }

        if (newActive !== this.activeLine) {
            this.activeLine = newActive;
            this._highlightLine(newActive);
        }
    }

    /**
     * Highlight dòng lyrics và auto-scroll
     * @private
     */
    _highlightLine(index) {
        const container = this._elements.container;
        if (!container) return;

        const lines = container.querySelectorAll('.lyrics-line');
        lines.forEach((el, i) => {
            el.classList.toggle('active', i === index);
            el.classList.toggle('past', i < index);
        });

        // Auto-scroll dòng hiện tại vào giữa
        if (index >= 0 && lines[index]) {
            lines[index].scrollIntoView({
                behavior: 'smooth',
                block: 'center',
            });
        }
    }

    /**
     * Render lyrics vào container
     * @private
     */
    _render() {
        const container = this._elements.container;
        if (!container) return;

        if (this.syncedLines.length > 0) {
            // Synced lyrics (LRC) — có timestamp, click-to-seek
            container.innerHTML = this.syncedLines.map((line, i) =>
                `<div class="lyrics-line" data-index="${i}" data-time="${line.time}">${this._escapeHtml(line.text)}</div>`
            ).join('');

            // Click vào dòng → seek đến thời điểm đó
            container.querySelectorAll('.lyrics-line').forEach(el => {
                el.addEventListener('click', () => {
                    const time = parseFloat(el.dataset.time);
                    player.seekTo(time);
                });
            });

        } else if (this.plainText) {
            // Plain text — không có timestamp
            container.innerHTML = `<div class="lyrics-plain">${
                this._escapeHtml(this.plainText).replace(/\n/g, '<br>')
            }</div>`;

        } else {
            // Không có lyrics
            container.innerHTML = `
                <div class="lyrics-empty">
                    <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                        <path d="m11 7.601-5.994 8.19a1 1 0 0 0 .1 1.298l.817.818a1 1 0 0 0 1.314.087L15.09 12"/>
                        <path d="M16.5 21.174C15.5 20.5 14.372 20 13 20c-2.058 0-3.928.755-4.782 1.9"/>
                        <path d="m6.5 15.5 3 3"/>
                        <path d="M21 5c-1 2-3 4-6 4"/>
                        <path d="M22 2 11 13"/>
                    </svg>
                    <span>Chưa có lời bài hát</span>
                </div>`;
        }
    }

    /**
     * Escape HTML entities
     * @private
     */
    _escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Toggle hiển thị lyrics panel
     */
    toggle() {
        this.isVisible = !this.isVisible;

        const { panel, toggleBtn, vinylContainer } = this._elements;

        if (panel) {
            panel.classList.toggle('visible', this.isVisible);
        }
        if (vinylContainer) {
            vinylContainer.classList.toggle('lyrics-active', this.isVisible);
        }
        if (toggleBtn) {
            toggleBtn.classList.toggle('active', this.isVisible);
        }

        // Force sync khi mở
        if (this.isVisible && this.syncedLines.length > 0) {
            const { currentTime } = player.getTimeInfo();
            this._syncToTime(currentTime);
        }
    }
}

const lyricsManager = new LyricsManager();
export default lyricsManager;
