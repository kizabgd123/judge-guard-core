// JudgeGuard Mobile Console Service Worker
const CACHE_NAME = 'judgeguard-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/manifest.json'
];

self.addEventListener('install', (evt) => {
  evt.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (evt) => {
  evt.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', (evt) => {
  if (evt.request.url.includes('/api/')) {
    evt.respondWith(fetch(evt.request));
    return;
  }
  evt.respondWith(
    caches.match(evt.request).then((res) => res || fetch(evt.request))
  );
});
