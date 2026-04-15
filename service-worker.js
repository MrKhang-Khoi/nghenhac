/**
 * Service Worker — Vinyl Noir Music Player
 * 
 * Chiến lược cache:
 * - App Shell (HTML, CSS, JS, icons): Cache-first
 * - Playlist JSON: Network-first (để có data mới nhất)
 * - Audio files: Chỉ cache khi user chọn "tải offline"
 * - Cover images: Cache-first sau lần đầu load
 */

const APP_CACHE = 'vinyl-noir-app-v1';
const COVER_CACHE = 'vinyl-noir-covers-v1';
const AUDIO_CACHE = 'vinyl-noir-audio-v1';

// Files cần cache cho app shell
const APP_SHELL_FILES = [
    './',
    './index.html',
    './manifest.json',
    './assets/css/style.css',
    './assets/js/app.js',
    './assets/js/player.js',
    './assets/js/playlist.js',
    './assets/js/ui.js',
    './assets/js/media-session.js',
    './assets/js/storage.js',
    './assets/js/utils.js',
    './assets/covers/default-cover.jpg'
];

// ===== INSTALL =====
self.addEventListener('install', (event) => {
    console.log('[SW] Cài đặt Service Worker...');
    event.waitUntil(
        caches.open(APP_CACHE)
            .then(cache => {
                console.log('[SW] Cache app shell');
                return cache.addAll(APP_SHELL_FILES);
            })
            .then(() => self.skipWaiting())
            .catch(err => {
                console.error('[SW] Lỗi cache app shell:', err);
            })
    );
});

// ===== ACTIVATE =====
self.addEventListener('activate', (event) => {
    console.log('[SW] Kích hoạt Service Worker');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames
                    .filter(name => {
                        // Xóa cache cũ nếu version thay đổi
                        return name.startsWith('vinyl-noir-app-') && name !== APP_CACHE;
                    })
                    .map(name => {
                        console.log('[SW] Xóa cache cũ:', name);
                        return caches.delete(name);
                    })
            );
        }).then(() => self.clients.claim())
    );
});

// ===== FETCH =====
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Chỉ xử lý same-origin requests
    if (url.origin !== self.location.origin) return;

    const requestPath = url.pathname;

    // 1. Playlist JSON — Network-first (để có data mới nhất khi online)
    if (requestPath.includes('playlist.json')) {
        event.respondWith(networkFirst(event.request, APP_CACHE));
        return;
    }

    // 2. Audio files — Cache-first (chỉ có trong cache nếu user đã tải offline)
    if (requestPath.includes('/assets/audio/')) {
        event.respondWith(cacheFirst(event.request, AUDIO_CACHE));
        return;
    }

    // 3. Cover images — Cache-first, network fallback
    if (requestPath.includes('/assets/covers/')) {
        event.respondWith(cacheFirstWithNetworkFallback(event.request, COVER_CACHE));
        return;
    }

    // 4. App shell (HTML, CSS, JS) — Cache-first
    event.respondWith(cacheFirst(event.request, APP_CACHE));
});

/**
 * Cache-first strategy
 * Ưu tiên lấy từ cache, nếu không có thì fetch từ network
 */
async function cacheFirst(request, cacheName) {
    try {
        const cached = await caches.match(request);
        if (cached) return cached;

        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (err) {
        const cached = await caches.match(request);
        if (cached) return cached;

        // Trả về offline fallback nếu là HTML
        if (request.headers.get('accept')?.includes('text/html')) {
            return caches.match('./index.html');
        }

        return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
    }
}

/**
 * Network-first strategy
 * Ưu tiên fetch từ network, nếu lỗi thì lấy cache
 */
async function networkFirst(request, cacheName) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (err) {
        const cached = await caches.match(request);
        if (cached) return cached;
        return new Response('[]', {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

/**
 * Cache-first với network fallback + tự động cache cover mới
 */
async function cacheFirstWithNetworkFallback(request, cacheName) {
    try {
        const cached = await caches.match(request);
        if (cached) return cached;

        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(cacheName);
            cache.put(request, response.clone());
        }
        return response;
    } catch (err) {
        const cached = await caches.match(request);
        if (cached) return cached;

        // Trả về default cover nếu cover không tải được
        return caches.match('./assets/covers/default-cover.jpg');
    }
}

// Lắng nghe message từ app (ví dụ: xóa cache)
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'CLEAR_AUDIO_CACHE') {
        caches.delete(AUDIO_CACHE).then(() => {
            event.ports[0]?.postMessage({ status: 'done' });
        });
    }

    if (event.data && event.data.type === 'GET_CACHE_KEYS') {
        caches.open(AUDIO_CACHE).then(cache => {
            return cache.keys();
        }).then(keys => {
            event.ports[0]?.postMessage({
                urls: keys.map(k => k.url)
            });
        });
    }
});
