const CACHE = "careermatch-v1";
const ASSETS = ["/", "/index.html", "/CareerMatch.png"];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  // Ne pas cacher les requetes API (toujours en live)
  if (event.request.url.includes("/api/")) return;
  event.respondWith(
    caches.match(event.request).then((res) => res || fetch(event.request))
  );
});