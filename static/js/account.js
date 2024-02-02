/* A function that retrieves session data from /session path
and replaces the values of navbar components with the corresponding values */
function getSessionData() {
    /* GET request to retrieve session data from /session path */
    return fetch('/session', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        })
        .then((response) => {
            if (response.ok) {
                return response.json();
            } else {
                throw new Error('Error fetching session data');
            }
        })
        .catch((error) => {
            console.error('Error:', error);
        });
}

function setElementTextFromSessionData(elementId, sessionDataPath) {
    const element = document.getElementById(elementId);
    if (element && sessionDataPath) {
        element.innerHTML = sessionDataPath;
    }
}

getSessionData().then((sessionData) => {
    const {
        userinfo
    } = sessionData;
    setElementTextFromSessionData("account-fullname", userinfo['name']);
    setElementTextFromSessionData("account-email", userinfo['email']);
    setElementTextFromSessionData("account-username", userinfo['preferred_username']);
    setElementTextFromSessionData("account-device", userinfo['deviceId']);
    setElementTextFromSessionData("account-gateway", userinfo['gatewayId']);
    setElementTextFromSessionData("account-dwelling", userinfo['dwellingId']);
    const pilotIdCapitalized = userinfo['pilotId'].charAt(0).toUpperCase() + userinfo['pilotId'].slice(1);
    setElementTextFromSessionData("account-pilot", pilotIdCapitalized);
});