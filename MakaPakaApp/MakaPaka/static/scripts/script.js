const GET = "GET";
const POST = "post";
const URL = "https://localhost:8080/";

const LOGIN_FIELD_ID = "login";
const PESEL_FIELD_ID = "pesel";
const PASSWORD_FIELD_ID = "password";
const RE_PASSWORD_FIELD_ID = "second_password";
const NAME_ID = "name";
const SURNAME_ID = "surname";
const BIRTHDATE_ID = "birthdate";
const CITY_ID = "city";
const STREET_ID = "street";
const NUMBER_ID = "number";
const POSTCODE_ID = "postcode";
const COUNTRY_ID = "country";

var HTTP_STATUS = { OK: 200, CREATED: 201, NOT_FOUND: 404 };

let registrationForm = document.getElementById("registration-form");
let loginField = document.getElementById(LOGIN_FIELD_ID);
let peselField = document.getElementById(PESEL_FIELD_ID);
let passwordField = document.getElementById(PASSWORD_FIELD_ID);
let secondPasswordField = document.getElementById(RE_PASSWORD_FIELD_ID);
let nameField = document.getElementById(NAME_ID);
let surnameField = document.getElementById(SURNAME_ID);
let birthdateField = document.getElementById(BIRTHDATE_ID);
let cityField = document.getElementById(CITY_ID);
let streetField = document.getElementById(STREET_ID);
let numberField = document.getElementById(NUMBER_ID);
let postcodeField = document.getElementById(POSTCODE_ID);
let countryField = document.getElementById(COUNTRY_ID);

let isLogAvailable;

prepareAllFieldsValidators();

registrationForm.addEventListener("submit", function (event) {
    event.preventDefault();

    console.log("Form submission stopped.");

    var n = event.srcElement.length;
    for (var i = 0; i < n; i++) {
        console.log(event.srcElement[i].value);
    }

    if (isLogAvailable && isProperSecondPassword() && isProperPassword()) {
        submitRegisterForm();
    } else {
        console.log("Nie rejestruję, bo pola nie są poprawne!");
    }
});

function submitRegisterForm() {
    let registerUrl = URL + "create";

    let registerParams = {
        method: POST,
        body: new URLSearchParams(new FormData(registrationForm)),
        redirect: "follow"
    };

    fetch(registerUrl, registerParams)
        .then(response => getRegisterResponseData(response))
        .then(response => displayInConsoleCorrectResponse(response))
        .catch(err => {
            console.log("Caught error: " + err);
        });
}

function getRegisterResponseData(response) {
    let status = response.status;

    console.log(response);

    if (status === HTTP_STATUS.OK || status === HTTP_STATUS.CREATED) {
        notifyAboutRegistration();
        clearForm();
        return response.json();
    } else {
        console.error("Response status code: " + response.status);
        throw "Unexpected response status: " + response.status;
    }
}

function displayInConsoleCorrectResponse(correctResponse) {
    let status = correctResponse.registration_status;

    console.log("Status: " + status);

    if (status !== "OK") {
        console.log("Errors: " + correctResponse.errors);
    }
}

function prepareAllFieldsValidators() {
    loginField.addEventListener("change", function () {
        var loginInput = loginField.value.trim();

        if (isProperLogin()) {
            console.log("spoko login");
            updateLoginAvailabilityMessage();
        }
        else if (loginInput.length > 0) {
            console.log("nie spoko");
            updateLoginAvailabilityMessage();
        }
        else if (loginInput.length == 0) {
            removeWarningMessage("loginWarning");
        }
    });

    passwordField.addEventListener("change", function () {
        var passwordInput = passwordField.value;
        let passWordInfo = ["Hasło musi zawierać:", "- małą literę", "- wielką literę", "- cyfrę", "- znak specjalny (!@#$%&*)"];

        updateFieldValidityMessage("passwordWarning", passWordInfo, PASSWORD_FIELD_ID);
        updateFieldValidityMessage("secondPasswordWarning", ["Hasła są różne"], RE_PASSWORD_FIELD_ID);

        if (passwordInput.length == 0) {
            removeWarningMessage("passwordWarning");
            removeWarningMessage("secondPasswordWarning");
        }
    });

    secondPasswordField.addEventListener("change", function () {
        var secondPasswordInput = secondPasswordField.value;
        updateFieldValidityMessage("secondPasswordWarning", ["Hasła są różne"], RE_PASSWORD_FIELD_ID);

        if (secondPasswordInput.length == 0) {
            removeWarningMessage("secondPasswordWarning");
        }
    });
}

function isProperLogin() {
    var login = loginField.value.trim();
    return login.length >= 4 && /^[a-zA-Z]+$/.test(login);
}

function isProperPassword() {
    var password = passwordField.value;
    var condition = new RegExp("^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#\$%&\*])(?=.{8,})");

    return condition.test(password);
}

function isProperSecondPassword() {
    var secondPassword = secondPasswordField.value;
    var firstPassword = passwordField.value;

    return firstPassword == secondPassword;
}

function showWarningMessage(newElemId, message, validatedElemID) {
    let warningElem = prepareWarningElem(newElemId, message);
    appendAfterElem(validatedElemID, warningElem);
}

function removeWarningMessage(warningElemId) {
    let warningElem = document.getElementById(warningElemId);

    if (warningElem !== null) {
        warningElem.remove();
    }
}

function appendAfterElem(currentElemId, newElem) {
    let currentElem = document.getElementById(currentElemId);
    currentElem.insertAdjacentElement('afterend', newElem);
}

function isLoginAvailable() {
    return Promise.resolve(checkLoginAvailability().then(function (statusCode) {
        console.log(statusCode);
        if (statusCode === HTTP_STATUS.OK) {
            isLogAvailable = false;
            return false;
        } else if (statusCode === HTTP_STATUS.NOT_FOUND) {
            isLogAvailable = true;
            return true;
        } else {
            throw "Unknown login availability status: " + statusCode;
        }
    }));
}

function checkLoginAvailability() {
    let loginInput = document.getElementById(LOGIN_FIELD_ID);
    let baseUrl = URL + "user/";
    let userUrl = baseUrl + loginInput.value;

    return Promise.resolve(fetch(userUrl, { method: GET }).then(function (resp) {
        return resp.status;
    }).catch(function (err) {
        return err.status;
    }));
}

function prepareWarningElem(newElemId, messages) {
    let warningField = document.getElementById(newElemId);

    if (warningField === null) {
        warningField = document.createElement('h5');
        warningField.setAttribute("id", newElemId);
        warningField.className = "warning-field";
    } else {
        warningField.innerHTML = "";
    }

    for (message of messages) {
        let textMessage = document.createTextNode(message);
        let breakLine = document.createElement('br');
        warningField.appendChild(textMessage);
        warningField.appendChild(breakLine);
    }

    warningField.removeChild(warningField.lastChild);
    return warningField;
}

function updateLoginAvailabilityMessage() {
    let warningElemId = "loginWarning";
    let warningAvailabilityMessage = "Login zajęty";

    isLoginAvailable().then(function (isAvailable) {
        if (!isAvailable) {
            showWarningMessage(warningElemId, [warningAvailabilityMessage], LOGIN_FIELD_ID);
        } else {
            removeWarningMessage(warningElemId);
        }
    }).catch(function (error) {
        console.error("Something went wrong while checking login.");
        console.error(error);
    });
}

function updateFieldValidityMessage(warningElemId, warningMessages, fieldID) {
    if (isProper(fieldID)) {
        removeWarningMessage(warningElemId);
    } else {
        showWarningMessage(warningElemId, warningMessages, fieldID);
    }

}

function isProper(fieldID) {
    if (fieldID == LOGIN_FIELD_ID) {
        return isProperLogin();
    }
    else if (fieldID == PESEL_FIELD_ID) {
        return isProperPesel();
    }
    else if (fieldID == PASSWORD_FIELD_ID) {
        return isProperPassword();
    }
    else if (fieldID == NAME_ID) {
        return isProperName();
    }
    else if (fieldID == SURNAME_ID) {
        return isProperSurname();
    }
    else if (fieldID == CITY_ID) {
        return isProperCity();
    }
    else if (fieldID == NUMBER_ID) {
        return isProperNumber();
    }
    else if (fieldID == COUNTRY_ID) {
        return isProperCountry();
    }
    else if (fieldID == POSTCODE_ID) {
        return isProperPostcode();
    }
    else if (fieldID == STREET_ID) {
        return isProperStreet();
    }
    else {
        return isProperSecondPassword();
    }
}

function clearForm() {
    loginField.value = "";
    peselField.value = "";
    passwordField.value = "";
    secondPasswordField.value = "";
    nameField.value = "";
    surnameField.value = "";
    birthdateField.value = "";
    cityField.value = "";
    numberField.value = "";
    streetField.value = "";
    postcodeField.value = "";
    countryField.value = "";
}

function notifyAboutRegistration() {
    if (document.getElementsByClassName("card")[0] == null) {
        let message = "Rejestracja przebiegła pomyślnie!";
        let textMessage = document.createTextNode(message);
        let notificationCard = document.createElement('div');
        let removeButton = document.createElement("a");
        removeButton.className = "btn btn-success";
        removeButton.innerHTML = "OK";
        notificationCard.className = "card";

        notificationCard.appendChild(textMessage);
        notificationCard.appendChild(removeButton);

        let registerButton = document.getElementsByClassName("button-form-submit")[0];
        registerButton.insertAdjacentElement("afterend", notificationCard);

        removeButton.addEventListener("click", function () {
            let notification = document.getElementsByClassName("card")[0];

            if (notification !== null) {
                notification.remove();
            }
        });
    }
}