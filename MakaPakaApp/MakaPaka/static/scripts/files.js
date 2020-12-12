function getData() {
    var tbody = document.getElementById("packages-body");
    const myParams = new URLSearchParams(window.location.search)

    fetch(`https://localhost:8080/GET/packages?fromIndex=${myParams.get('fromIndex')}&toIndex=${myParams.get('toIndex')}`)
        .then(resp => resp.json())
        .then(info => {
            prepareButtons(info.prev, info.next)
            return info.files
        })
        .then(data => {
            tbody.innerHTML = ''
            for (let info in data) {
                tbody.innerHTML +=
                    '<tr><td>' + info
                    + '</td><td class="centered-col">' + data[info][1]
                    + `<td class="centered-col"><a href="https://localhost:8081/package/${info}"><button class="btn btn-success">Otwórz</button></a></td>`

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
            if (+myParams.get('toIndex') + 1 < Object.keys(files).length || Object.keys(files).length % 4 !== 0) {
                buttonsPlace.innerHTML += `<a href="${next}"><button class="btn btn-primary">Następne</button></a>`
            }
        })
}

getData()