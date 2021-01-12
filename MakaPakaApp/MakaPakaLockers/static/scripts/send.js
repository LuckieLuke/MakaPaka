const SEND_FORM = document.getElementById('send-form')
SEND_FORM.addEventListener('submit', e => {
    e.preventDefault()

    var formData = new FormData()
    formData.append('locker', e.srcElement[0].value)
    formData.append('package', e.srcElement[1].value)

    var courierUrl = 'https://localhost:8087/senddata'

    var actionParams = {
        method: 'POST',
        body: formData
    }

    fetch(courierUrl, actionParams)
        .then(resp => resp.status)
        .then(status => {
            if (status == 200) {
                sendPackage(formData.get('locker'), formData.get('package'))
            }
        })
        .catch(err => console.log(err))
})
function sendPackage(lockerID, packageID) {
    (async () => {
        await socket.emit('join', { 'room_id': packageID, 'useragent': navigator.userAgent })
        await socket.emit('putin', { 'package_id': packageID, 'locker_id': lockerID, 'useragent': navigator.userAgent })
        change()
    })()
}

function change() {
    const locker = document.getElementById('locker')
    const package = document.getElementById('package')

    locker.value = ''
    package.value = ''
}

document.addEventListener("DOMContentLoaded", function (event) {
    var ws_uri = 'https://localhost:8090'
    socket = io.connect(ws_uri)

    socket.on('put_in_locker', () => {
        const msgField = document.getElementById('msg-h6');
        msgField.innerHTML = 'Paczka dodana do paczkomatu'
    })
})