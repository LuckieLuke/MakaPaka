var ws_uri = 'https://localhost:8090'
socket = io.connect(ws_uri)


const SEND_FORM = document.getElementsByClassName('take-form')[0]
SEND_FORM.addEventListener('submit', e => {
    e.preventDefault()

    var formData = new FormData()
    formData.append('package', e.srcElement[0].value)

    var courierUrl = 'https://localhost:8085/takepackage'

    var actionParams = {
        method: 'POST',
        body: formData
    }

    const msg = document.getElementById('msg')
    const formInput = document.getElementsByClassName('form-control')[0]
    fetch(courierUrl, actionParams)
        .then(resp => {
            formInput.value = ''
            if (resp.ok) {
                msg.innerHTML = 'Paczka odebrana!'
                return resp.json()
            } else {
                msg.innerHTML = 'Paczka nie posiada statusu nowej!'
                return { 'package': 'niemapaczki' }
            }
        })
        .then(info => {
            takenPackage(info['package'])
        })
        .catch(err => console.log(err))
})

const takenPackage = async (name) => {
    await socket.emit('join', { 'room_id': name, 'useragent': navigator.userAgent })
    await socket.emit('take_from_sender', { 'package_id': name, 'useragent': navigator.userAgent })
}