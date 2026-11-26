/* 資料助秘 密碼查找器 — Service Worker（線上/手機版離線快取）
   注意：每次改到快取內容，請遞增 CACHE 版本號，使用者才會拿到新檔。 */
const CACHE = "pwfinder-v1.0.0";
const ASSETS = [
  "./",
  "index.html",
  "css/style.css",
  "js/app.js",
  "js/options.js",
  "js/voice.js",
  "js/local.js",
  "vendor/zip-full.min.js",
  "manifest.webmanifest",
  "assets/icon.svg",
  "assets/icon-180.png",
  "assets/icon-192.png",
  "assets/icon-512.png",
  "assets/icon-maskable.png",
  "assets/voice/welcome.mp3",
  "assets/voice/wifi.mp3",
  "assets/voice/text.mp3",
  "assets/voice/archive.mp3",
  "assets/voice/office.mp3",
  "assets/voice/star.mp3",
  "assets/voice/mail.mp3",
  "assets/voice/found.mp3",
  "assets/voice/voiceon.mp3",
];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  // 後端 API 不快取（線上版本就沒有 API，直接讓它失敗→前端走純前端）
  if (url.pathname.startsWith("/api/")) return;
  e.respondWith(
    caches.match(e.request).then((hit) => hit || fetch(e.request).then((res) => {
      // 同源成功回應順手快取
      if (res.ok && url.origin === self.location.origin) {
        const copy = res.clone();
        caches.open(CACHE).then((c) => c.put(e.request, copy));
      }
      return res;
    }).catch(() => hit))
  );
});
