self.addEventListener("install", (event) => {
  console.log("Gorlanews SW installato");
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  console.log("Gorlanews SW attivato");
  return self.clients.claim();
});

// Per ora nessuna cache e nessuna gestione notifiche.
// Aggiungeremo push e notificationclick più avanti.
