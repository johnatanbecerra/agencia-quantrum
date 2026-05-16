const CACHE_NAME = 'quantrum-cache-v2';
const ASSETS = [
  './',
  './index.html',
  './nosotros.html',
  './desarrollo-web.html',
  './aplicaciones-pwa.html',
  './diseno-ui-ux.html',
  './ecommerce.html',
  './optimizacion-seo.html',
  './backend-apis.html',
  './quantrum_logo.png',
  './video_equipo.mp4'
];

// Instalar el Service Worker y guardar en caché la estructura esencial
self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS);
    }).then(() => self.skipWaiting())
  );
});

// Activar el componente y limpiar versiones viejas de caché (v1)
self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Servir desde la caché para máxima velocidad
self.addEventListener('fetch', (e) => {
  e.respondWith(
    caches.match(e.request).then((cachedResponse) => {
      return cachedResponse || fetch(e.request);
    })
  );
});