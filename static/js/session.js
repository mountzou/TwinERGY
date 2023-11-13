/* A function to get the response for the session data, as retrieved
from the route /session function implemented in the app.py. */
function getSessionData() {
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

/* A function to get the response for the device status data, as retrieved
from the route /get_device_status function implemented in the app.py. */
function getDeviceStatus() {
    fetch('/get_device_status')
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        console.log('Device Status:', data.device_status);
        data.device_status > 0 ? wearable_device_on() : wearable_device_off();
    })
    .catch(error => {
        console.error('There has been a problem with your fetch operation:', error);
    });
}

/* A function to handle with active (ON state) wearable device status */
function wearable_device_on() {
    var element = document.getElementById("device-status");
    element && (element.textContent = "Active");
}

/* A function to handle with inactive (OFF state) wearable device status */
function wearable_device_off() {
    var element = document.getElementById("device-status");
    element && (element.textContent = "Inactive");
}

/* A function to set the text of HTML components regarding the building ID, wearable ID, username */
function updateSessionInformation(sessionData) {
    document.getElementById("building-id").innerHTML = sessionData['userinfo']['dwellingId'] + ', ' + sessionData['userinfo']['pilotId'].charAt(0).toUpperCase() + sessionData['userinfo']['pilotId'].slice(1);
    document.getElementById("wearable-id").innerHTML = sessionData['userinfo']['deviceId'];
    document.getElementById("username-id").innerHTML = 'Welcome, ' + sessionData['userinfo']['preferred_username'];
}

/* Insert the building ID, wearable ID, username to the corresponding components */
getSessionData().then(updateSessionInformation).catch((error) => {
    console.error('Error processing session data:', error);
});

/* Initial execution of the function to get the status of the wearable device */
getDeviceStatus();

/* Re-execution of the function to get the status of the wearable device every 10 sec. */
setInterval(getDeviceStatus, 10000);
