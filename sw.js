// Service Worker: macht die App installierbar und offline nutzbar.
// App-Dateien: sofort aus dem Cache, im Hintergrund aktualisieren.
// Ziehungsdaten (CSV): immer zuerst aus dem Netz, offline aus dem Cache.
const VERSION = 'kc-v2';
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/favicon-32.png',
  './icons/apple-touch-icon.png',
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  if (url.pathname.endsWith('.csv')) {
    // Netz zuerst, damit neue Ziehungen sofort da sind
    event.respondWith(
      fetch(req).then(res => {
        if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req.url, copy)); }
        return res;
      }).catch(() => caches.match(req.url).then(r => r || Promise.reject(new Error('offline'))))
    );
    return;
  }

  if (url.origin === location.origin) {
    // Cache zuerst, im Hintergrund auffrischen (Updates gelten beim nächsten Öffnen)
    event.respondWith(
      caches.open(VERSION).then(async cache => {
        const cached = await cache.match(req, { ignoreSearch: true });
        const network = fetch(req).then(res => {
          if (res.ok) cache.put(req, res.clone());
          return res;
        }).catch(() => cached);
        return cached || network;
      })
    );
  }
});
