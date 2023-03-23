function convertToPercentage(value) {
  var percentage = (1 - Math.abs(value) / 3) * 100;
  return percentage.toFixed(2);
}

var graphTargetAirTemperature = $("#daily-temperature");
var graphTargetHumidity = $("#daily-humidity");
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