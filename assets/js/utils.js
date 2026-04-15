/**
 * utils.js — Các hàm tiện ích dùng chung
 * Vinyl Noir Music Player
 */

/**
 * Format giây thành chuỗi mm:ss
 * @param {number} seconds - Số giây
 * @returns {string} Chuỗi dạng "mm:ss"
 */
export function formatTime(seconds) {
    if (!seconds || isNaN(seconds) || seconds < 0) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Debounce function — giới hạn tần suất gọi hàm
 * @param {Function} func - Hàm cần debounce
 * @param {number} delay - Độ trễ ms
 * @returns {Function} Hàm đã debounce
 */
export function debounce(func, delay = 300) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

/**
 * Throttle function — giới hạn tối đa 1 lần gọi mỗi khoảng thời gian
 * @param {Function} func - Hàm cần throttle
 * @param {number} limit - Khoảng thời gian ms
 * @returns {Function} Hàm đã throttle
 */
export function throttle(func, limit = 100) {
    let inThrottle = false;
    return function (...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => { inThrottle = false; }, limit);
        }
    };
}

/**
 * Sanitize tên file — bỏ ký tự đặc biệt
 * @param {string} filename - Tên file gốc
 * @returns {string} Tên file đã sanitize
 */
export function sanitizeFilename(filename) {
    return filename
        .replace(/[<>:"/\\|?*]/g, '')
        .replace(/\s+/g, '_')
        .replace(/_+/g, '_')
        .trim();
}

/**
 * Format bytes thành chuỗi đọc được (KB, MB, GB)
 * @param {number} bytes - Số bytes
 * @returns {string} Chuỗi dạng "X.X MB"
 */
export function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const unitIndex = Math.floor(Math.log(bytes) / Math.log(1024));
    const value = (bytes / Math.pow(1024, unitIndex)).toFixed(1);
    return `${value} ${units[unitIndex]}`;
}

/**
 * Tạo ID ngắn gọn từ chuỗi
 * @param {string} text - Chuỗi gốc
 * @returns {string} ID dạng slug
 */
export function generateId(text) {
    return text
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/đ/g, 'd')
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-|-$/g, '')
        .substring(0, 50);
}

/**
 * Kiểm tra URL có hợp lệ không
 * @param {string} url - URL cần kiểm tra
 * @returns {boolean}
 */
export function isValidUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}
