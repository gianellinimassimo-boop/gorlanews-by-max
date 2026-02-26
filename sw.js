self.addEventListener("install", (event) => {
  console.log("Gorlanews service worker installato");
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  console.log("Gorlanews service worker attivato");
  return self.clients.claim();
});

// In futuro qui potremo aggiungere:
// - cache delle pagine per offline
// - gestione delle notifiche push
