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

// A function that matches the VOC index to a literal description
function getWellBeingDescription(value) {
  if (0 <= value && value <= 150) {
    return "Good";
  } else if (151 <= value && value <= 230) {
    return "Moderate";
  } else if (231 <= value && value <= 300) {
    return "Unhealthy for Sensitive Groups";
  } else if (301 <= value && value <= 400) {
    return "Unhealthy";
  } else if (401 <= value && value <= 450) {
    return "Very Unhealthy";
  } else if (451 <= value && value <= 500) {
    return "Hazardous";
  } else {
    return "Invalid input value";
  }
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

function updateDashboard() {
    $.getJSON('/get_data_thermal_comfort/', function (data) {
        let temperature = data.daily_thermal_comfort_data.map(x => x[0]);
        let humidity = data.daily_thermal_comfort_data.map(x => x[1]);
        let voc_index = data.daily_thermal_comfort_data.map(x => x[3]);
        let time = data.daily_thermal_comfort_data.map(x => unixToHumanReadable(x[2]));
        let met = data.daily_thermal_comfort_data.map(x => x[4]);
        let pmv = data.daily_thermal_comfort_data.map(x => x[5]);
        let clo = data.daily_thermal_comfort_data.map(x => x[6]);

        let latestTemperature = temperature[temperature.length - 1];
        let latestHumidity = humidity[humidity.length - 1];
        let latestVocIndex = voc_index[voc_index.length - 1];
        let latestVocDesc = getWellBeingDescription(voc_index[voc_index.length - 1]);
        let latestTime = time[time.length - 1];
        let latestMet = met[met.length - 1];
        let latestPMV = pmv[pmv.length - 1];
        let latestClo = clo[clo.length - 1];

        // Update the latest temperature and humidity
        document.getElementById("latest-indoor-temperature").innerHTML = latestTemperature + ' °C';
        document.getElementById("latest-indoor-humidity").innerHTML = latestHumidity + ' %';
        document.getElementById("latest-voc-index").innerHTML = latestVocIndex + ' voc. index';
        document.getElementById("latest-voc-desc").innerHTML = latestVocDesc;
        document.getElementById("latest-met").innerHTML = latestMet.toFixed(2) + ' met';
        document.getElementById("latest-clo").innerHTML = latestClo + ' clo';
        document.getElementById("latest-PMV").innerHTML = latestPMV;
        document.getElementById("latest-PMV-desc").innerHTML = get_pmv_status(latestPMV);

        let sum_tem = 0, sum_voc = 0, sum_hum = 0;

        data.daily_thermal_comfort_data.reduce((accumulator, currentValue) => {
            sum_tem += currentValue[0];
            sum_voc += currentValue[3];
            sum_hum += currentValue[1];
        }, 0);

        let mean_temp = parseFloat((sum_tem / data.daily_thermal_comfort_data.length).toFixed(2));
        let mean_hum = parseFloat((sum_hum / data.daily_thermal_comfort_data.length).toFixed(2));
        let mean_voc = parseFloat((sum_voc / data.daily_thermal_comfort_data.length).toFixed(2));

        // Update the mean temperature, humidity and VOC index
        document.getElementById("daily-mean-temperature").innerHTML = mean_temp+' °C';
        document.getElementById("daily-mean-humidity").innerHTML = mean_hum+' %';
        document.getElementById("daily-mean-vocs").innerHTML = mean_voc+' voc.';

        Array.from(document.getElementsByClassName("l-updated")).forEach(element => {
            element.innerHTML = 'Latest update at ' + latestTime;;
        });

        var graphTargetAirTemperature = $("#daily-temperature");
        var graphTargetHumidity = $("#daily-humidity");
        var graphTargetWB = $("#daily-VOC");
        var graphTargetThermalComfort = $("#latest-thermal-comfort");

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

        var indoorWB = {
            labels: time,
            datasets: [{
                label: "VOC Index",
                type: "line",
                borderColor: "rgb(255, 186, 77)",
                backgroundColor: "rgb(255, 186, 77, .1)",
                borderWidth: 3,
                data: voc_index,
                fill: true
            }]
        };

        var thermalComfort = {
            labels: ["Comfort", "Discomfort"],
            datasets: [{
                label: "Thermal Comfort",
                data: [convertPMVToPercentage(latestPMV), (100-convertPMVToPercentage(latestPMV)).toFixed(2)],
                backgroundColor: [
                    "#ffba4d",
                    "#EEEEEE",
                ]
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

        var barGraph = new Chart(graphTargetThermalComfort, {
            type: 'doughnut',
            data: thermalComfort,
            options: {
                elements: {
                    arc: {
                        roundedCornersFor: 0
                    }
                }
            }
        });

        var graphWB = new Chart(graphTargetWB, {
            type: 'line',
            data: indoorWB,
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
                                return value + " voc.";
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
                },
                tooltips: {
                    callbacks: {
                        label: function(tooltipItems, data) {
                            return data.datasets[tooltipItems.datasetIndex].label +': ' + tooltipItems.yLabel;
                        }
                    }
                }
            }
        });

    });
}

updateDashboard();

setInterval(updateDashboard, 8000);