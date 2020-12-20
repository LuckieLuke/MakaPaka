Projekt uruchamiany jest poleceniem `docker-compose up`

- aplikacja dla nadawcy - port 8080
- aplikacja dla kuriera - port 8085
- aplikacja paczkomatu - port 8087

Przy pierwszym uruchomieniu proszę o wejście pod adres 'https://localhost:8080/generate', aby wygenerować 5 kurierów oraz 5 paczkomatów.
Paczkomaty są nazywane odpowiednio locker0, locker1, ..., locker4.
Każdy kurier dostaje login courier0, courier1, ..., courier4 i hasło, będące jednocześnie loginem. 

Jako że aplikacja kurierska jest PWA, należy ją testować, używając Google Chrome z flagami:
 --ignore-certificate-errors --unsafely-treat-insecure-origin-as-secure=https://localhost:8085 --allow-insecure-localhost https://localhost:8085