var prevURL = '';
var nextURL = '';
const saveButton = document.getElementById("save");

saveButton.addEventListener("click", function () {
    window.location.href = 'http://localhost:8085/options'
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

    fetch(`http://localhost:8085/GET/packages?fromIndex=${myParams.get('fromIndex')}&toIndex=${myParams.get('toIndex')}`)
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
                    <label class="label-group">${package}</label>
                </div>
                `
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

    fetch(`http://localhost:8085/GET/packages?fromIndex=0&toIndex=-1`)
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