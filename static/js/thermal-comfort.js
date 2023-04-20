// A function that convert the PMV index to percentage for the donut chart of dashboard
function convertPMVToPercentage(value) {
  var percentage = (1 - Math.abs(value) / 3) * 100;
  return percentage.toFixed(2);
}

// A function that converts the timestamp to human readable form
function unixToHumanReadable(unixTimestamp) {
    let date = new Date(unixTimestamp * 1000);
    return date.toLocaleString();
}

// A function that matches the PMV index to a literal description
function get_pmv_status(pmv) {
  const status_dict = new Map([
    [[-2.5, -1.5], 'Cool'],
    [[-1.5, -0.5], 'Slightly Cool'],
    [[-0.5, 0.5], 'Neutral'],
    [[0.5, 1.5], 'Slightly Warm'],
    [[1.5, 2.5], 'Warm']
  ]);

  for (const [prange, status] of status_dict.entries()) {
    if (prange[0] <= pmv && pmv < prange[1]) {
      return status;
    }
  }

  if (pmv < -2.5) {
    return 'Cold';
  } else if (pmv > 2.5) {
    return 'Hot';
  } else {
    return '-';
  }
}

var today = new Date();
var start_date_1 = new Date(today.getFullYear(), today.getMonth(), today.getDate());
var end_date_1 = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);

var start_date = start_date_1.toISOString().substr(0, 10);
var end_date = end_date_1.toISOString().substr(0, 10);

function updateThermalComfort() {
    $.getJSON('/get_data_thermal_comfort_range', {'start_date': start_date, 'end_date': end_date}, function (data) {
        let temperature = data.map(x => x[0]);
        let humidity = data.map(x => x[1]);
        let time = data.map(x => unixToHumanReadable(x[2]));
        let met = data.map(x => x[4]);

        let latestTemperature = temperature[temperature.length - 1];
        let latestHumidity = humidity[humidity.length - 1];
        let latestTime = time[time.length - 1];
        let latestMet = met[met.length - 1]

        // Update the latest temperature and humidity
        document.getElementById("latest-indoor-temperature").innerHTML = latestTemperature + ' °C';
        document.getElementById("latest-indoor-humidity").innerHTML = latestHumidity + ' %';
        document.getElementById("latest-met").innerHTML = latestMet + ' met';

        let sum_tem = data.reduce((accumulator, currentValue) => {
            return accumulator + currentValue[0];
        }, 0);

        let sum_hum = data.reduce((accumulator, currentValue) => {
            return accumulator + currentValue[1];
        }, 0);

        let sum_met = data.reduce((accumulator, currentValue) => {
            return accumulator + currentValue[4];
        }, 0);

        let mean_temp = parseFloat((sum_tem / data.length).toFixed(2));
        let mean_hum = parseFloat((sum_hum / data.length).toFixed(2));
        let mean_met = parseFloat((sum_met / data.length).toFixed(2));

        // Update the mean  temperature and humidity
        document.getElementById("daily-mean-temperature").innerHTML = mean_temp+' °C';
        document.getElementById("daily-mean-humidity").innerHTML = mean_hum+' %';
        document.getElementById("daily-mean-met").innerHTML = mean_met+' met';

        // Select all elements with the class "l-updated"
        let time_elements = document.getElementsByClassName("l-updated");

        // Update the innerHTML of all elements with the "l-updated" class
        for (let i = 0; i < time_elements.length; i++) {
            time_elements[i].innerHTML = 'Latest update at '+latestTime;
        }

        var graphTargetAirTemperature = $("#chart-temperature");
        var graphTargetHumidity = $("#chart-humidity");
        var graphTargetMetabolic = $("#chart-met");

        var indoorTemperature = {
            labels: time,
            datasets: [{
                label: "Air Temperature",
                type: "line",
                borderColor: "rgb(255, 186, 77)",
                backgroundColor: "rgb(255, 186, 77, .1)",
                borderWidth: 3,
                data: temperature,
                fill: true
            }]
        };

        var indoorHumidity = {
            labels: time,
            datasets: [{
                label: "Relative Humidity",
                type: "line",
                borderColor: "rgb(255, 186, 77)",
                backgroundColor: "rgb(255, 186, 77, .1)",
                borderWidth: 3,
                data: humidity,
                fill: true
            }]
        };

        var indoorMetabolic = {
            labels: time,
            datasets: [{
                label: "Metabolic Rate",
                type: "line",
                borderColor: "rgb(255, 186, 77)",
                backgroundColor: "rgb(255, 186, 77, .1)",
                borderWidth: 3,
                data: met,
                fill: true
            }]
        };

        var graphTemperature = new Chart(graphTargetAirTemperature, {
            type: 'line',
            data: indoorTemperature,
            options: {
                animation: false,
                scales: {
                    yAxes: [{
                        ticks: {
                            padding: 12,
                            fontFamily: "Josefin Sans",
                            beginAtZero: false,
                            autoSkip: true,
                            maxTicksLimit: 5,
                            callback: function(value, index, values) {
                                return value + " °C";
                            },
                        }
                    }],
                    xAxes: [{
                        gridLines: {
                            display: false,
                            drawOnChartArea: true
                        },
                        ticks: {
                            display: false,
                        }
                    }],
                },
                legend: {
                    onClick: function(e) {
                        e.stopPropagation();
                    }
                }
            }
        });

        var graphHumidity = new Chart(graphTargetHumidity, {
            type: 'line',
            data: indoorHumidity,
            options: {
                animation: false,
                scales: {
                    yAxes: [{
                        ticks: {
                            padding: 12,
                            fontFamily: "Josefin Sans",
                            beginAtZero: false,
                            autoSkip: true,
                            maxTicksLimit: 5,
                            callback: function(value, index, values) {
                                return value + " %";
                            },
                        }
                    }],
                    xAxes: [{
                        gridLines: {
                            display: false,
                            drawOnChartArea: true
                        },
                        ticks: {
                            display: false,
                        }
                    }],
                },
                legend: {
                    onClick: function(e) {
                        e.stopPropagation();
                    }
                }
            }
        });

        var graphMetabolic = new Chart(graphTargetMetabolic, {
            type: 'line',
            data: indoorMetabolic,
            options: {
                animation: false,
                scales: {
                    yAxes: [{
                        ticks: {
                            padding: 12,
                            fontFamily: "Josefin Sans",
                            beginAtZero: false,
                            autoSkip: true,
                            maxTicksLimit: 5,
                            callback: function(value, index, values) {
                                return value + " met";
                            },
                        }
                    }],
                    xAxes: [{
                        gridLines: {
                            display: false,
                            drawOnChartArea: true
                        },
                        ticks: {
                            display: false,
                            maxTicksLimit: 4,
                            maxRotation: 0,
                            minRotation: 0
                        }
                    }],
                },
                legend: {
                    onClick: function(e) {
                        e.stopPropagation();
                    }
                }
            }
        });

    });
}

updateThermalComfort();

setInterval(updateThermalComfort, 8000);