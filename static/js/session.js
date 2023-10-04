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

/* Replace the content of HTML components related to session's information */
getSessionData().then((sessionData) => {
    document.getElementById("building-id").innerHTML = sessionData['userinfo']['dwellingId'] + ', '  + sessionData['userinfo']['pilotId'].charAt(0).toUpperCase() + sessionData['userinfo']['pilotId'].slice(1);
    document.getElementById("wearable-id").innerHTML = sessionData['userinfo']['deviceId'];
    document.getElementById("username-id").innerHTML = 'Welcome, ' + sessionData['userinfo']['preferred_username'];
});


var status = 'inactive';

var redDot = document.querySelector('.red-dot');
var liveText = document.querySelector('#live-id');

redDot.style.backgroundColor = 'white';
liveText.innerHTML = 'Searching..';

let previousStatus = null;

function checkForNewData() {
  $.getJSON('/get_device_status', function (data) {
    let currentTimestamp = Math.floor(Date.now() / 1000);

    if (data === null) {
      console.log('Data is null!');
    } else {
      if (data[0] === 0) {
        status = 'init';
      } else if (-12 < currentTimestamp - data[0] && currentTimestamp - data[0] < 12) {
          if (previousStatus !== 'active') {

          }
          status = 'active';
      } else {
        if (previousStatus !== 'inactive') {

        }
        status = 'inactive';
      }
      previousStatus = status;
    }

    switch (status) {
      case 'active':
        redDot.style.animationIterationCount = 'infinite';
        redDot.style.backgroundColor = 'white';
        liveText.textContent = 'Active';
        break;
      case 'inactive':
        redDot.style.backgroundColor = '#1e2727';
        redDot.style.animationIterationCount = '0';
        liveText.textContent = 'Inactive';
        break;
      case 'init':
        redDot.style.animationIterationCount = 'infinite';
        redDot.style.backgroundColor = '#FFF7D4';
        liveText.textContent = 'Initializing...';
        break;
      default:
        throw new Error(`Unknown status: ${status}`);
    }
  });
}
checkForNewData();
// Call the checkForNewData function every minute
setInterval(checkForNewData, 2500);