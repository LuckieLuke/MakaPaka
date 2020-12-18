const clockPlace = document.getElementsByClassName('clock')[0]
const codePlace = document.getElementsByClassName('code')[0]
var timeLeft = 60

async function generate() {
    let logged = await setCode()

    if (logged === true) {
        clockPlace.innerHTML = 'Kod ważny przez: ' + timeLeft + ' sekund'
        const clock = setInterval(() => {
            timeLeft--
            clockPlace.innerHTML = 'Kod ważny przez: ' + timeLeft + ' sekund'
            if ((timeLeft > 20 || timeLeft < 10) && timeLeft % 10 > 0 && timeLeft % 10 < 5 && timeLeft !== 1) {
                clockPlace.innerHTML += 'y'
            } else if (timeLeft === 1) {
                clockPlace.innerHTML += 'ę'
            }

            if (timeLeft <= 0) {
                clearInterval(clock)
                clockPlace.innerHTML = 'Kod wygasł'
                putButton()
                timeLeft = 60
            }
        }, 1000)
    }
}

async function setCode() {
    const resp = await fetch('https://localhost:8085/GET/code');
    const data = await resp.json();

    if (data.code === 'Zaloguj się!') {
        codePlace.innerHTML = `<a href="https://localhost:8085/">${data.code}</a>`
        clockPlace.innerHTML = ''
    } else {
        codePlace.innerHTML = data.code
    }

    return data.code !== 'Zaloguj się!'
}

function putButton() {
    codePlace.innerHTML = '<button id="generate" class="button" onclick="generate()"><span>Generuj kod</span></button>'
}