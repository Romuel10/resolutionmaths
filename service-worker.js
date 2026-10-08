const CACHE='resolutionmaths-local-v1';
const CORE=['./','./index.html','./styles.css','./app.js','./worker.js','./solver.py','./icon.svg','./manifest.webmanifest'];
self.addEventListener('install',ev=>{ev.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(CORE)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',ev=>{ev.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',ev=>{const url=new URL(ev.request.url);if(ev.request.method!=='GET'||url.origin!==self.location.origin)return;ev.respondWith(caches.match(ev.request).then(cached=>cached||fetch(ev.request).then(response=>{if(response.ok){const clone=response.clone();caches.open(CACHE).then(c=>c.put(ev.request,clone));}return response;})));});
