function convertToPercentage(value) {
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

const categories = all_wb.map(getWellBeingDescription);
const categoryCounts = {};

categories.forEach((category) => {
  categoryCounts[category] = (categoryCounts[category] || 0) + 1;
});

// Target the html chart items for air temperature, relative humidity, VOC and thermal comfort, respectively
//var graphTargetWBAgg = $("#daily-VOC-agg");

//var indoorWBAgg = {
//    labels: Object.keys(categoryCounts),
//    datasets: [{
//        label: "Daily VOC Aggregated",
//        type: "bar",
//        borderColor: "rgb(255, 186, 77, .4)",
//        backgroundColor: "rgb(255, 186, 77, .5)",
//        barPercentage: 0.5,
//        barThickness: 10,
//        maxBarThickness: 15,
//        minBarLength: 9,
//        data: Object.values(categoryCounts),
//    }]
//};

//var graphWBAgg = new Chart(graphTargetWBAgg, {
//  type: 'bar',
//  data: indoorWBAgg,
//  options: {
//        scales: {
//            yAxes: [{
//                type: 'logarithmic',
//                ticks: {
//                    padding: 12,
//                    fontFamily: "Josefin Sans",
//                    beginAtZero: false,
//                    autoSkip: true,
//                    maxTicksLimit: 4,
//                    callback: function(value, index, values) {
//                        return value + " times";
//                    },
//                }
//            }],
//            xAxes: [{
//                gridLines: {
//                    display: false,
//                    drawOnChartArea: true
//                },
//                ticks: {
//                    display: true,
//                },
//            }],
//        },
//        legend: {
//            onClick: function(e) {
//                e.stopPropagation();
//            }
//        },
//        tooltips: {
//            callbacks: {
//                label: function(tooltipItems, data) {
//                    return data.datasets[tooltipItems.datasetIndex].label +': ' + tooltipItems.yLabel;
//                }
//            }
//        }
//    }
//});

function updateDashboard() {
    $.getJSON('/as_test', function (data) {
        let temperature = data.map(x => x[0]);
        let humidity = data.map(x => x[1]);
        let voc_index = data.map(x => x[3]);
        let time = data.map(x => unixToHumanReadable(x[2]));

        let latestTemperature = temperature[temperature.length - 1];
        let latestHumidity = humidity[humidity.length - 1];
        let latestTime = time[time.length - 1];

        console.log(latestTime)

        // Update the latest temperature and humidity
        document.getElementById("latest-indoor-temperature").innerHTML = latestTemperature+' °C';
        document.getElementById("latest-indoor-humidity").innerHTML = latestHumidity+' %';

        let sum_tem = data.reduce((accumulator, currentValue) => {
            return accumulator + currentValue[0];
        }, 0);

        let sum_hum = data.reduce((accumulator, currentValue) => {
            return accumulator + currentValue[1];
        }, 0);

        let mean_temp = parseFloat((sum_tem / data.length).toFixed(2));
        let mean_hum = parseFloat((sum_hum / data.length).toFixed(2));

        // Update the mean  temperature and humidity
        document.getElementById("daily-mean-temperature").innerHTML = mean_temp+' °C';
        document.getElementById("daily-mean-humidity").innerHTML = mean_hum+' %';

        // Select all elements with the class "example-class"
        let time_elements = document.getElementsByClassName("l-updated");

        // Update the innerHTML of all elements with the "example-class" class
        for (let i = 0; i < time_elements.length; i++) {
            time_elements[i].innerHTML = 'Latest update at '+latestTime;
        }

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
                data: [convertToPercentage(l_pmv), 100-convertToPercentage(l_pmv)],
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