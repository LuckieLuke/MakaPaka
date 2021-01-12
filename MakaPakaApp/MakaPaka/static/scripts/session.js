const LOGIN_FORM = document.getElementsByClassName('login-form')[0]

LOGIN_FORM.addEventListener('submit', e => {
    e.preventDefault()

    let formData = new FormData()
    formData.append('login', e.srcElement[0].value)
    formData.append('password', e.srcElement[1].value)

    let authUrl = 'https://localhost:8082/auth'

    let actionParams = {
        method: 'POST',
        body: formData
    }

    const formInputs = document.getElementsByClassName('form-input')
    const msg = document.getElementById('msg')
    fetch(authUrl, actionParams)
        .then(resp => {
            if (resp.ok) {
                sessionStorage.setItem('username', e.srcElement[0].value)
                setTimeout(() => {
                    window.location.href = 'https://localhost:8080'
                }, 1000);
            } else {
                for (let input of formInputs) {
                    input.value = ''
                }
                msg.innerHTML = 'Niepoprawny login lub hasło!'
            }
        })
})