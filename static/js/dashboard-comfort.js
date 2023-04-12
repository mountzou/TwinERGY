function convertToPercentage(value) {
  var percentage = (1 - Math.abs(value) / 3) * 100;
  return percentage.toFixed(2);
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
var graphTargetAirTemperature = $("#daily-temperature");
var graphTargetHumidity = $("#daily-humidity");
var graphTargetWB = $("#daily-VOC");
var graphTargetWBAgg = $("#daily-VOC-agg");
var graphTargetThermalComfort = $("#latest-thermal-comfort");

var indoorTemperature = {
    labels: all_times,
    datasets: [{
        label: "Air Temperature",
        type: "line",
        borderColor: "rgb(255, 186, 77)",
        backgroundColor: "rgb(255, 186, 77, .1)",
        borderWidth: 3,
        data: all_tem,
        fill: true
    }]
};

var indoorHumidity = {
    labels: all_times,
    datasets: [{
        label: "Relative Humidity",
        type: "line",
        borderColor: "rgb(255, 186, 77)",
        backgroundColor: "rgb(255, 186, 77, .1)",
        borderWidth: 3,
        data: all_hum,
        fill: true
    }]
};

var indoorWB = {
    labels: all_times,
    datasets: [{
        label: "VOC Index",
        type: "line",
        borderColor: "rgb(255, 186, 77)",
        backgroundColor: "rgb(255, 186, 77, .1)",
        borderWidth: 3,
        data: all_wb,
        fill: true
    }]
};

var indoorWBAgg = {
    labels: Object.keys(categoryCounts),
    datasets: [{
        label: "Daily VOC Aggregated",
        type: "bar",
        borderColor: "rgb(255, 186, 77, .4)",
        backgroundColor: "rgb(255, 186, 77, .5)",
        barPercentage: 0.5,
        barThickness: 10,
        maxBarThickness: 15,
        minBarLength: 9,
        data: Object.values(categoryCounts),
    }]
};

var graphTemperature = new Chart(graphTargetAirTemperature, {
    type: 'line',
    data: indoorTemperature,
    options: {
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

var graphWBAgg = new Chart(graphTargetWBAgg, {
  type: 'bar',
  data: indoorWBAgg,
  options: {
        scales: {
            yAxes: [{
                type: 'logarithmic',
                ticks: {
                    padding: 12,
                    fontFamily: "Josefin Sans",
                    beginAtZero: false,
                    autoSkip: true,
                    maxTicksLimit: 4,
                    callback: function(value, index, values) {
                        return value + " times";
                    },
                }
            }],
            xAxes: [{
                gridLines: {
                    display: false,
                    drawOnChartArea: true
                },
                ticks: {
                    display: true,
                },
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