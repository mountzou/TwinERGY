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

var graphTargetAirTemperature = $("#daily-temperature");
var graphTargetHumidity = $("#daily-humidity");

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
        },
        tooltips: {
            enabled: false,
            callbacks: {
                title: function(tooltipItems, data) {
                    return 'Time: ' + tooltipItems[0].xLabel;
                },
                label: function(tooltipItems, data) {
                    return tooltipItems.yLabel + ' °C';
                },
            }
        },
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
        },
        tooltips: {
            enabled: false,
            callbacks: {
                title: function(tooltipItems, data) {
                    return 'Time: ' + tooltipItems[0].xLabel;
                },
                label: function(tooltipItems, data) {
                    return tooltipItems.yLabel + ' %';
                },
            }
        },
    }
});