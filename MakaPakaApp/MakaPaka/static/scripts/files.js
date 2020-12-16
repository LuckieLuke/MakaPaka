function getData() {
    var tbody = document.getElementById("packages-body");
    const myParams = new URLSearchParams(window.location.search)

    fetch(`https://localhost:8080/GET/packages?fromIndex=${myParams.get('fromIndex')}&toIndex=${myParams.get('toIndex')}`, { method: "GET" })
        .then(resp => resp.json())
        .then(info => {
            prepareButtons(info.prev, info.next, Object.keys(info.files).length)
            return info.files
        })
        .then(data => {
            tbody.innerHTML = ''
            for (let info in data) {
                tbody.innerHTML +=
                    '<tr><td>' + info.slice(0, -4)
                    + '</td><td class="centered-col">' + data[info][1]
                    + '</td><td class="centered-col">' + data[info][2]
                    + `<td class="centered-col buttons-col"><a href="https://localhost:8081/package/${info}" class="btn btn-success action-buttons">Otwórz</a>`
                    + `<button onclick="deleteFile('${info}')" class="btn btn-danger action-buttons" ${data[info][2] !== 'nowa' ? 'disabled' : null}>Usuń</button></td></tr>`
            }
        })
}

function prepareButtons(prev, next, filesNum) {
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
            console.log(+myParams.get('toIndex'))
            console.log(Object.keys(files).length)
            if (+myParams.get('toIndex') < Object.keys(files).length - 1) {
                buttonsPlace.innerHTML += `<a href="${next}"><button class="btn btn-primary">Następne</button></a>`
            }
        })
}

function deleteFile(name) {
    let deleteURL = `https://localhost:8080/package/delete/${name}`

    let params = {
        method: 'DELETE',
        body: { "name": name }
    };

    fetch(deleteURL, params)
        .then(response => {
            if (response.redirected) {
                window.location.href = 'https://localhost:8080/packages?fromIndex=0&toIndex=3'
            }
            else { response.json() }
        }
        )
        .catch(err => {
            console.log("Caught error: " + err);
        });
}

getData()