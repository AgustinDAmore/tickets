// tickets/static/js/push-setup.js

async function subscribeUser() {
    // Reemplaza esto con tu clave pública real de settings.py
    const vapidPublicKey = "Pega_tu_VAPID_PUBLIC_KEY_aquí";
    const convertedVapidKey = urlBase64ToUint8Array(vapidPublicKey);

    try {
        const subscription = await navigator.serviceWorker.ready
            .then(registration => {
                return registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: convertedVapidKey
                });
            });

        // Obtenemos el token CSRF de la página
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

        // Enviar la suscripción al backend de Django
        await fetch('/webpush/save_information/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify(subscription),
        });
        console.log('Usuario suscrito a notificaciones push.');

    } catch (error) {
        console.error('Error al suscribir al usuario:', error);
    }
}

// --- Funciones auxiliares (no necesitas modificarlas) ---
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

async function setupPushNotifications() {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        try {
            await navigator.serviceWorker.register('/static/js/serviceworker.js');
            const permission = await window.Notification.requestPermission();
            if (permission === 'granted') {
                console.log('Permiso de notificación concedido.');
                await subscribeUser();
            }
        } catch (error) {
            console.error('Error en el Service Worker:', error);
        }
    }
}

// Iniciar el proceso cuando se carga la página
window.addEventListener('load', () => {
    setupPushNotifications();
});