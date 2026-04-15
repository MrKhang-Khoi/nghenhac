/**
 * icons.js — Lucide SVG Icon Definitions
 * Vinyl Noir Music Player
 * 
 * Tập trung toàn bộ SVG icons để đảm bảo đồng nhất,
 * sắc nét trên mọi thiết bị. Thay thế emoji Unicode.
 * 
 * Source: https://lucide.dev (MIT License)
 */

/**
 * Tạo SVG icon string với kích thước tùy chỉnh
 * @param {string} paths - Inner SVG paths
 * @param {number} size - Kích thước icon (px)
 * @param {object} opts - Options: fill, strokeWidth, className
 * @returns {string} SVG markup
 */
function icon(paths, size = 24, opts = {}) {
    const {
        fill = 'none',
        strokeWidth = 2,
        className = '',
        viewBox = '0 0 24 24'
    } = opts;
    return `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}" viewBox="${viewBox}" fill="${fill}" stroke="currentColor" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round" class="icon ${className}">${paths}</svg>`;
}

// ===== PLAYER CONTROLS =====

export const ICON_PLAY = (size = 24) => icon(
    `<polygon points="6 3 20 12 6 21 6 3" fill="currentColor" stroke="none"/>`,
    size, { fill: 'none' }
);

export const ICON_PAUSE = (size = 24) => icon(
    `<rect x="5" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/><rect x="15" y="4" width="4" height="16" rx="1" fill="currentColor" stroke="none"/>`,
    size, { fill: 'none' }
);

export const ICON_SKIP_BACK = (size = 24) => icon(
    `<polygon points="19 20 9 12 19 4 19 20"/><line x1="5" y1="19" x2="5" y2="5"/>`,
    size
);

export const ICON_SKIP_FORWARD = (size = 24) => icon(
    `<polygon points="5 4 15 12 5 20 5 4"/><line x1="19" y1="5" x2="19" y2="19"/>`,
    size
);

// ===== PLAY MODES =====

export const ICON_REPEAT = (size = 24) => icon(
    `<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>`,
    size
);

export const ICON_REPEAT_ONE = (size = 24) => icon(
    `<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/><text x="12" y="15.5" text-anchor="middle" font-size="8" font-weight="700" fill="currentColor" stroke="none" font-family="var(--font-display, sans-serif)">1</text>`,
    size
);

export const ICON_SHUFFLE = (size = 24) => icon(
    `<path d="M2 18h1.4c1.3 0 2.5-.6 3.3-1.7l6.1-8.6c.7-1.1 2-1.7 3.3-1.7H22"/><path d="m18 2 4 4-4 4"/><path d="M2 6h1.9c1.5 0 2.9.9 3.6 2.2"/><path d="M22 18h-5.9c-1.3 0-2.6-.7-3.3-1.8l-.5-.8"/><path d="m18 14 4 4-4 4"/>`,
    size
);

export const ICON_ARROW_RIGHT = (size = 24) => icon(
    `<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>`,
    size
);

// ===== HEART / FAVORITE =====

export const ICON_HEART_OUTLINE = (size = 24) => icon(
    `<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>`,
    size
);

export const ICON_HEART_FILLED = (size = 24) => icon(
    `<path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>`,
    size, { fill: 'currentColor' }
);

// ===== VOLUME =====

export const ICON_VOLUME_HIGH = (size = 24) => icon(
    `<path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"/><path d="M16 9a5 5 0 0 1 0 6"/><path d="M19.364 18.364a9 9 0 0 0 0-12.728"/>`,
    size
);

export const ICON_VOLUME_LOW = (size = 24) => icon(
    `<path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"/><path d="M16 9a5 5 0 0 1 0 6"/>`,
    size
);

export const ICON_VOLUME_MUTE = (size = 24) => icon(
    `<path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"/><line x1="22" y1="9" x2="16" y2="15"/><line x1="16" y1="9" x2="22" y2="15"/>`,
    size
);

// ===== UI / NAVIGATION =====

export const ICON_SEARCH = (size = 24) => icon(
    `<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>`,
    size
);

export const ICON_SETTINGS = (size = 24) => icon(
    `<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>`,
    size
);

export const ICON_X = (size = 24) => icon(
    `<path d="M18 6 6 18"/><path d="m6 6 12 12"/>`,
    size
);

export const ICON_MUSIC = (size = 24) => icon(
    `<path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/>`,
    size
);

export const ICON_HEADPHONES = (size = 24) => icon(
    `<path d="M3 14h3a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a9 9 0 0 1 18 0v7a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3"/>`,
    size
);

export const ICON_LIST_MUSIC = (size = 24) => icon(
    `<path d="M21 15V6"/><path d="M18.5 18a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z"/><path d="M12 12H3"/><path d="M16 6H3"/><path d="M12 18H3"/>`,
    size
);

export const ICON_CHECK_CIRCLE = (size = 24) => icon(
    `<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>`,
    size
);

export const ICON_DOWNLOAD = (size = 24) => icon(
    `<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>`,
    size
);

export const ICON_TRASH = (size = 24) => icon(
    `<path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/>`,
    size
);

export const ICON_INFO = (size = 24) => icon(
    `<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>`,
    size
);

export const ICON_SAVE = (size = 24) => icon(
    `<path d="M15.2 3a2 2 0 0 1 1.4.6l3.8 3.8a2 2 0 0 1 .6 1.4V19a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/><path d="M17 21v-7a1 1 0 0 0-1-1H8a1 1 0 0 0-1 1v7"/><path d="M7 3v4a1 1 0 0 0 1 1h7"/>`,
    size
);

export const ICON_WIFI_OFF = (size = 24) => icon(
    `<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>`,
    size
);

export const ICON_WIFI = (size = 24) => icon(
    `<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>`,
    size
);
