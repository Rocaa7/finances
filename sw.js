// Primer la xarxa (sempre la versió nova); si no hi ha connexió, la còpia guardada.
const C = 'fin-v8';
self.addEventListener('install', e => e.waitUntil(
  caches.open(C).then(c => c.addAll(['./', 'index.html', 'manifest.webmanifest', 'icon-192.png', 'icon-512.png'])).then(() => self.skipWaiting())));
self.addEventListener('activate', e => e.waitUntil(
  caches.keys().then(ks => Promise.all(ks.filter(k => k !== C && k !== 'share').map(k => caches.delete(k)))).then(() => self.clients.claim())));
self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // fitxer compartit des d'una altra app (manifest share_target): el desem i obrim l'app
  if (e.request.method === 'POST' && url.pathname.endsWith('/share')) {
    e.respondWith((async () => {
      const f = (await e.request.formData()).get('csv');
      if (f) await (await caches.open('share')).put('shared.csv', new Response(f));
      return Response.redirect('./?shared=1', 303);
    })());
    return;
  }
  if (e.request.method !== 'GET' || url.origin !== location.origin) return; // preus: sempre de la xarxa
  e.respondWith(caches.open(C).then(c =>
    fetch(e.request, { cache: 'no-cache' }).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; })
      .catch(() => c.match(e.request))));
});
