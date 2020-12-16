var prevURL = '';
var nextURL = '';
const saveButton = document.getElementById("save");

saveButton.addEventListener("click", function () {
    var packages = []
    var archive = allStorage()
    for (let package in archive) {
        if (archive[package] === 'true') {
            packages.push(package)
        }
    }

    var courierUrl = 'https://localhost:8087/POST/takepackages'

    var actionParams = {
        method: 'POST',
        body: JSON.stringify(packages),
        headers: {
            'Content-Type': 'application/json'
        },
    }

    fetch(courierUrl, actionParams)
        .then(resp => resp.json())
        .catch(err => console.log(err))

    window.location.href = 'https://localhost:8087/'

})

function allStorage() {
    var archive = {},
        keys = Object.keys(localStorage),
        i = 0, key

    for (; key = keys[i]; i++) {
        archive[key] = localStorage.getItem(key)
    }

    return archive
}

function getData() {
    var packages = document.getElementsByClassName("containers")[0];
    const myParams = new URLSearchParams(window.location.search)

    fetch(`https://localhost:8087/GET/packages?fromIndex=${myParams.get('fromIndex')}&toIndex=${myParams.get('toIndex')}&locker=${myParams.get('locker')}`)
        .then(resp => resp.json())
        .then(info => {
            prepareButtons(info.prev, info.next)
            return info.packages
        })
        .then(data => {
            packages.innerHTML = ''
            for (let package of data) {
                packages.innerHTML += `
                <div class="choice">
                    <label class="label-group">${package.length > 15 ? package.slice(0, 15) + '...' : package}
                        <input type="checkbox" id="${package}" class="files" name="${package}" ${localStorage.getItem(package) === 'true' ? "checked" : null}/>
                        <span class="checkmark"></span>
                    </label>
                </div>
                `
            }
            const checkboxes = document.getElementsByClassName('files');

            for (let checkbox of checkboxes) {
                checkbox.addEventListener('change', (e) => {
                    if (e.target.checked === true) {
                        localStorage.setItem(checkbox.id, true);
                    } else {
                        localStorage.removeItem(checkbox.id)
                    }
                })
            }
        })
}

getData()

function prepareButtons(prev, next) {
    const prevButton = document.getElementById('prev')
    const nextButton = document.getElementById('next')
    const myParams = new URLSearchParams(window.location.search)

    prevURL = prev;
    nextURL = next;

    if (+myParams.get('fromIndex') <= 0) {
        prevButton.setAttribute('disabled', true)
    } else {
        prevButton.removeAttribute('disabled')
    }

    fetch(`https://localhost:8087/GET/packages?fromIndex=0&toIndex=-1&locker=${myParams.get('locker')}`)
        .then(resp => resp.json())
        .then(info => info.packages)
        .then(data => {
            if (+myParams.get('toIndex') < data.length - 1) {
                nextButton.removeAttribute('disabled')
            } else {
                nextButton.setAttribute('disabled', true)
            }
        })

}

function previous() {
    window.location.href = prevURL
    getData()
}

function next() {
    window.location.href = nextURL
    getData()
}