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
function checkForNewData() {
  $.getJSON('/get_device_status', function (data) {

    let currentTimestamp = Math.floor(Date.now() / 1000);
    if (data[0][0]===0){
        status='init'
    }
    else{
       if (-12< currentTimestamp - data[0][0] && currentTimestamp - data[0][0] < 12) {
        status = 'active';
        }
        else {
        status='inactive';
        }
    }
    var redDot = document.querySelector('.red-dot');
    var liveText = document.querySelector('#live-id');

    if (status === 'active') {
      redDot.style.backgroundColor = 'white';
      liveText.textContent = 'Active';
    } else if (status === 'inactive') {
      redDot.style.backgroundColor = 'gray';
      liveText.textContent = 'Inactive';
    } else {
        redDot.style.backgroundColor = 'red';
      liveText.textContent = 'Initializing';
    }
  });
}

//document.addEventListener('DOMContentLoaded', function() {
//  var redDot = document.querySelector('.red-dot');
//  var liveText = document.querySelector('#live-id');
//  var status = 'inactive'; // Assume this variable is set elsewhere in the program
//  if (status === 'active') {
//    redDot.style.backgroundColor = 'green';
//    liveText.textContent = 'On Wrist - Active';
//  } else if (status === 'inactive') {
//    redDot.style.backgroundColor = 'gray';
//    liveText.textContent = 'On Wrist - Inactive';
//  } else {
//    redDot.style.backgroundColor = 'red';
//    liveText.textContent = 'On Wrist - Error';
//  }
//});



// Call the checkForNewData function every minute
setInterval(checkForNewData, 2500);