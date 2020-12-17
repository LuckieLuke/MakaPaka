if ('serviceWorker' in navigator) {
    navigator.serviceWorker
        .register('../service-worker.js')
        .then(function () { console.log("ServiceWorker correctly registered"); })
        .catch(err => console.log(err));
}