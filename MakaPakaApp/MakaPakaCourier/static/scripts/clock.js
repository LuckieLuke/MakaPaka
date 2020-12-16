const clockPlace = document.getElementsByClassName('clock')[0]
var timeLeft = 25;

clockPlace.innerHTML = timeLeft + ' sekund';

const clock = setInterval(() => {
    timeLeft--
    clockPlace.innerHTML = timeLeft + ' sekund'
    if ((timeLeft > 20 || timeLeft < 10) && timeLeft % 10 > 0 && timeLeft % 10 < 5 && timeLeft !== 1) {
        clockPlace.innerHTML += 'y'
    } else if (timeLeft === 1) {
        clockPlace.innerHTML += 'a'
    }

    if (timeLeft <= 0) {
        clearInterval(clock)
    }
}, 1000)