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

getSessionData().then((sessionData) => {
    document.getElementById("account-fullname").innerHTML = sessionData['userinfo']['name'];
    document.getElementById("account-email").innerHTML = sessionData['userinfo']['email'];
    document.getElementById("account-username").innerHTML = sessionData['userinfo']['preferred_username'];
    document.getElementById("account-device").innerHTML = sessionData['userinfo']['deviceId'];
    document.getElementById("account-gateway").innerHTML = sessionData['userinfo']['gatewayId'];
    document.getElementById("account-dwelling").innerHTML = sessionData['userinfo']['dwellingId'];
    document.getElementById("account-pilot").innerHTML = sessionData['userinfo']['pilotId'].charAt(0).toUpperCase() + sessionData['userinfo']['pilotId'].slice(1);
});