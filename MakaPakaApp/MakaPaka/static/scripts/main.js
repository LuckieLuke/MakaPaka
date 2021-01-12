setSession()

async function setSession() {
    const resp = await fetch('https://localhost:8080/GET/username')
    if (resp.ok) {
        const data = await resp.json()
        sessionStorage.setItem('username', data['username'])
    }
}