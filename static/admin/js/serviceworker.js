// tickets/static/js/serviceworker.js

self.addEventListener('push', function(event) {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/admin/img/icon-alert.svg', // Opcional: un ícono para la notificación
        data: {
            url: data.url // URL a la que se redirigirá al hacer clic
        }
    };
    event.waitUntil(
        self.registration.showNotification(data.head, options) // Usamos 'head' para el título
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data.url)
    );
});