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
    document.getElementById("building-id").innerHTML = sessionData['userinfo']['dwellingId']+ ', ' +sessionData['userinfo']['pilotId'];
    document.getElementById("wearable-id").innerHTML = sessionData['userinfo']['deviceId'];
    document.getElementById("username-id").innerHTML = 'Welcome, '+sessionData['userinfo']['preferred_username'];
});