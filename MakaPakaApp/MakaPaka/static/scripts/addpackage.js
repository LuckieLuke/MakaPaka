const SEND_FORM = document.getElementsByClassName('waybills-form')[0]
SEND_FORM.addEventListener('submit', e => {
    e.preventDefault()

    var formData = new FormData()
    formData.append('sender_name', e.srcElement[0].value)
    formData.append('sender_surname', e.srcElement[1].value)
    formData.append('sender_phone', e.srcElement[2].value)
    formData.append('sender_street', e.srcElement[3].value)
    formData.append('sender_city', e.srcElement[4].value)
    formData.append('sender_code', e.srcElement[5].value)
    formData.append('sender_country', e.srcElement[6].value)
    formData.append('recipient_name', e.srcElement[7].value)
    formData.append('recipient_surname', e.srcElement[8].value)
    formData.append('recipient_phone', e.srcElement[9].value)
    formData.append('recipient_street', e.srcElement[10].value)
    formData.append('recipient_city', e.srcElement[11].value)
    formData.append('recipient_code', e.srcElement[12].value)
    formData.append('recipient_country', e.srcElement[13].value)

    for (let i = 0; i < 14; i++) {
        e.srcElement[i].value = ''
    }

    const photoField = document.getElementById('photo')
    formData.append('photo', photoField.files[0])

    var courierUrl = 'https://localhost:8080/addpackage'

    var actionParams = {
        method: 'POST',
        body: formData
    }

    var name = '';

    fetch(courierUrl, actionParams)
        .then(resp => resp.json())
        .then(info => {
            name = info['name'].slice(0, -4);
            (async (name) => {
                await socket.emit('join', { 'room_id': name, 'useragent': navigator.userAgent })
                await socket.emit('new_package', { 'room_id': sessionStorage.getItem('username'), 'useragent': navigator.userAgent })
            })()
        })
        .catch(err => console.log(err))

    setTimeout(() => {
        goBack()
    }, 1000)
})

var ws_uri = 'https://localhost:8090'
socket = io.connect(ws_uri)
socket.emit('join', { 'room_id': sessionStorage.getItem('username'), 'useragent': navigator.userAgent })

function goBack() {
    window.location.href = 'https://localhost:8080/packages?fromIndex=0&toIndex=3'
}