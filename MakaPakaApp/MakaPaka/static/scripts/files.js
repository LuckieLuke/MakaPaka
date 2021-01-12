function getData() {
    var tbody = document.getElementById("packages-body");
    const myParams = new URLSearchParams(window.location.search)

    fetch(`https://localhost:8080/GET/packages?fromIndex=${myParams.get('fromIndex')}&toIndex=${myParams.get('toIndex')}`, { method: "GET" })
        .then(resp => resp.json())
        .then(info => {
            prepareButtons(info.prev, info.next)
            return info.files
        })
        .then(data => {
            tbody.innerHTML = ''
            for (let info in data) {
                socket.emit('join', { 'room_id': info.slice(0, -4), 'useragent': navigator.userAgent })
                tbody.innerHTML +=
                    '<tr><td>' + info.slice(0, -4)
                    + '</td><td class="centered-col">' + data[info][1]
                    + `</td><td class="centered-col" id="${info.slice(0, -4)}_status">` + data[info][2]
                    + `<td class="centered-col buttons-col"><a href="https://localhost:8081/package/${info}" class="btn btn-success action-buttons">Otwórz</a>`
                    + `<button onclick="deleteFile('${info}')" class="btn btn-danger action-buttons" id="${info.slice(0, -4)}_del" ${data[info][2] !== 'nowa' ? 'disabled' : null}>Usuń</button></td></tr>`
            }
        })
}

function prepareButtons(prev, next) {
    const myParams = new URLSearchParams(window.location.search)
    const buttonsPlace = document.getElementsByClassName('files-buttons')[0]
    buttonsPlace.innerHTML = ''

    if (myParams.get('fromIndex') > 0) {
        buttonsPlace.innerHTML += `<a href="${prev}"><button class="btn btn-primary">Poprzednie</button></a>`
    }

    fetch('https://localhost:8080/GET/packages?fromIndex=0&toIndex=-1')
        .then(resp => resp.json())
        .then(info => info.files)
        .then(files => {
            if (+myParams.get('toIndex') < Object.keys(files).length - 1) {
                buttonsPlace.innerHTML += `<a href="${next}"><button class="btn btn-primary">Następne</button></a>`
            }
        })
}

async function deleteFile(name) {
    let deleteURL = `https://localhost:8080/DELETE/package/${name}`

    let params = {
        method: 'DELETE',
        body: { "name": name }
    };

    const response = await fetch(deleteURL, params)
    if (response.ok) {
        socket.emit('new_package', { 'room_id': sessionStorage.getItem('username'), 'useragent': navigator.userAgent })
        window.location.replace('https://localhost:8080/packages?fromIndex=0&toIndex=3')
    }
    else { response.json() }
}

getData()

var ws_uri = 'https://localhost:8090'
socket = io.connect(ws_uri)
socket.emit('join', { 'room_id': sessionStorage.getItem('username'), 'useragent': navigator.userAgent })

socket.on('put_in_locker', (data) => {
    let statusField = document.getElementById(`${data['package_id']}_status`)
    let delButton = document.getElementById(`${data['package_id']}_del`)
    statusField.innerHTML = 'oczekująca w paczkomacie'
    delButton.setAttribute('disabled', true)
})

socket.on('refresh_packages', () => {
    window.location.reload()
})

socket.on('take_from_locker', (data) => {
    let statusField = document.getElementById(`${data['package_id']}_status`)
    statusField.innerHTML = 'odebrana z paczkomatu'
    let delButton = document.getElementById(`${data['package_id']}_del`)
    delButton.setAttribute('disabled', true)
})

socket.on('take_from_sender', (data) => {
    let statusField = document.getElementById(`${data['package_id']}_status`)
    statusField.innerHTML = 'przekazana kurierowi'
    let delButton = document.getElementById(`${data['package_id']}_del`)
    delButton.setAttribute('disabled', true)
})