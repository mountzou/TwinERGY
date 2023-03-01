function convertToPercentage(value) {
  var percentage = (1 - Math.abs(value) / 3) * 100;
  return percentage.toFixed(2);
}

var graphTargetAirTemperature = $("#daily-temperature");
var graphTargetHumidity = $("#daily-humidity");
var graphTargetThermalComfort = $("#latest-thermal-comfort");

var indoorTemperature = {
    labels: daily_time,
    datasets: [{
        label: "Air Temperature",
        type: "line",
        borderColor: "#7fdd62",
        backgroundColor: "#7fdd62",
        borderWidth: 3,
        data: daily_temp,
        fill: false
    }]
};

var indoorHumidity = {
    labels: daily_time,
    datasets: [{
        label: "Air Temperature",
        type: "line",
        borderColor: "#7fdd62",
        backgroundColor: "#7fdd62",
        borderWidth: 3,
        data: daily_hum,
        fill: false
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
        data: [convertToPercentage(latest_pmv), 100-convertToPercentage(latest_pmv)],
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