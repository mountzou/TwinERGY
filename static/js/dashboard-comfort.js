// Variables to store chart instances
let graphTemperature, graphHumidity, graphMetRate, graphPMV, graphVOC;

// A function that converts the timestamp to human readable form
function unixToHumanReadable(unixTimestamp) {
    let date = new Date(unixTimestamp * 1000);
    return date.toLocaleString();
}

// A function that matches the VOC index to a literal description
function getWellBeingDescription(value) {
    const wellBeingRanges = [
        { range: [0, 150], description: "Good" },
        { range: [151, 230], description: "Moderate" },
        { range: [231, 300], description: "Unhealthy for Sensitive Groups" },
        { range: [301, 400], description: "Unhealthy" },
        { range: [401, 450], description: "Very Unhealthy" },
        { range: [451, 2000], description: "Hazardous" }
    ];

    const found = wellBeingRanges.find(({ range }) => range[0] <= value && value <= range[1]);
    return found ? found.description : "Out of standard's range";
}

// A function that convert the PMV index to percentage for the donut chart of dashboard
function convertPMVToPercentage(value) {
    var percentage = (1 - Math.abs(value) / 3) * 100;
    return percentage.toFixed(2);
}

// A function that matches the PMV index to a literal description
function get_pmv_status(pmv) {
    const statusList = [
        { check: val => val < -2.5, status: 'Cold' },
        { range: [-2.5, -1.5], status: 'Cool' },
        { range: [-1.5, -0.5], status: 'Slightly Cool' },
        { range: [-0.5, 0.5], status: 'Neutral' },
        { range: [0.5, 1.5], status: 'Slightly Warm' },
        { range: [1.5, 2.5], status: 'Warm' },
        { check: val => val > 2.5, status: 'Hot' }
    ];

    const found = statusList.find(({ range, check }) =>
        check ? check(pmv) : range[0] <= pmv && pmv < range[1]
    );

    return found ? found.status : '-';
}

// An abstract function to create line charts in the dashboard page
function createLineChartData(label, data, time) {
    return {
        labels: time,
        datasets: [{
            label: label,
            type: "line",
            borderColor: "rgb(255, 186, 77)",
            backgroundColor: "rgba(255, 186, 77, .1)",
            borderWidth: 3,
            data: data,
            fill: true
        }]
    };
}

// An abstract function to set the configuration parameters for the line charts in the dashboard page
function createLineChartConfig(graphTarget, data, yAxisUnit, tooltipLabelCallback) {
    return new Chart(graphTarget, {
        type: 'line',
        data: data,
        options: {
            animation: false,
            scales: {
                y: {
                    ticks: {
                        padding: 12,
                        fontFamily: "Josefin Sans",
                        suggestedMin: Math.min(...data.datasets[0].data) - 0.5,
                        suggestedMax: Math.max(...data.datasets[0].data) + 0.5,
                        beginAtZero: false,
                        autoSkip: true,
                        maxTicksLimit: 5,
                        callback: function(value) {
                            return value + " " + yAxisUnit;
                        },
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawOnChartArea: true
                    },
                    ticks: {
                        display: false,
                    }
                },
            },
            plugins: {
                legend: {
                    onClick: function(e) {
                        e.stopPropagation();
                    }
                },
                tooltip: {
                    callbacks: {
                        label: tooltipLabelCallback
                    }
                }
            }
        }
    });
}

function createLineChartConfigPMV(graphTarget, data, categories, tooltipLabelCallback) {
    return new Chart(graphTarget, {
        type: 'line',
        data: data,
        options: {
            animation: false,
            scales: {
                y: {
                    ticks: {
                        padding: 12,
                        fontFamily: "Josefin Sans",
                        suggestedMin: 0,
                        suggestedMax: 7,
                        beginAtZero: false,
                        autoSkip: false,
                        maxTicksLimit: 17,
                        callback: function(value) {
                            return categories[value - 1];
                        },
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawOnChartArea: true
                    },
                    ticks: {
                        display: false,
                    }
                },
            },
            plugins: {
                legend: {
                    onClick: function(e) {
                        e.stopPropagation();
                    }
                },
                tooltip: {
                    callbacks: {
                        label: tooltipLabelCallback
                    }
                }
            }
        }
    });
}

function updateDashboard() {
    $.getJSON('/get_data_thermal_comfort/', function (data) {
        let [temperature, humidity, time, voc_index, met, pmv, clo, t_wearable, pmv_desc] = data.daily_thermal_comfort_data.reduce((acc, x) => {
            acc[0].push(x[0]);
            acc[1].push(x[1]);
            acc[2].push(unixToHumanReadable(x[2]));
            acc[3].push(x[3]);
            acc[4].push(x[4]);
            acc[5].push(x[5]);
            acc[6].push(x[6]);
            acc[7].push(x[7]);
            acc[8].push(get_pmv_status(x[5]));
            return acc;
        }, [[], [], [], [], [], [], [], [], []]);

        let latestTemperature = temperature.at(-1);
        let latestHumidity = humidity.at(-1);
        let latestTime = time.at(-1);
        let latestVocIndex = voc_index.at(-1);
        let latestVocDesc = getWellBeingDescription(voc_index.at(-1));
        let latestMet = met.at(-1);
        let latestPMV = pmv.at(-1);
        let latestClo = clo.at(-1);
        let latestTWearable = t_wearable.at(-1);
        console.log(pmv);

        // Update the latest temperature and humidity
        document.getElementById("latest-temperature").innerHTML = '≈ ' + latestTemperature + ' °C';
        document.getElementById("latest-humidity").innerHTML = '≈ ' + latestHumidity + ' %';
        document.getElementById("latest-voc-index").innerHTML = latestVocIndex + ' voc. index';
        document.getElementById("latest-voc-desc").innerHTML = latestVocDesc;
        document.getElementById("latest-met").innerHTML = latestMet + ' met';
        document.getElementById("latest-pmv").innerHTML = latestPMV;
//        document.getElementById("daily-mean-vocs").innerHTML = 20+' voc.';

        Array.from(document.getElementsByClassName("l-updated")).forEach(element => {
            element.innerHTML = 'Latest update at ' + latestTime;
        });

        var graphTargetTemperature = $("#session-temperature")[0];
        var graphTargetHumidity = $("#session-humidity")[0];
        var graphTargetMetabolic = $("#session-metabolic")[0];
        var graphTargetPMV = $("#session-thermal-comfort")[0];
        var graphTargetVOC = $("#session-VOC")[0];

        const fangerScaleMapping = {
            'Cold': 1,
            'Cool': 2,
            'Slightly Cool': 3,
            'Neutral': 4,
            'Slightly Warm': 5,
            'Warm': 6,
            'Hot': 7
        };

        // ---------------------
        // START OF SECTION: IMPLEMENTATION OF THE DASHBOARD LINE CHARTS
        // ---------------------

        // Implement the line chart in dashboard for the PMV
        const fangerScaleCategories = Object.keys(fangerScaleMapping);
        const numericalData = pmv_desc.map(item => fangerScaleMapping[item]);

        // Destroy previous chart instance if exists
        if (graphPMV) {
            graphPMV.destroy();
        }

        // Create the chart data
        var dataThermalComfort = createLineChartData("Thermal Comfort", numericalData, time);
        const thermalComfortTooltipCallback = (tooltipItems) => fangerScaleCategories[tooltipItems.raw - 1];

        // Create the chart
        graphPMV = createLineChartConfigPMV(graphTargetPMV, dataThermalComfort, fangerScaleCategories, thermalComfortTooltipCallback);

        // Implement the line chart in dashboard for the air temperature
        if (graphTemperature) {
            graphTemperature.destroy();
        }
        var dataTemperature = createLineChartData("Air Temperature", temperature, time);
        const temperatureTooltipCallback = (tooltipItems) => tooltipItems.raw.toFixed(2) + " °C";
        graphTemperature = createLineChartConfig(graphTargetTemperature, dataTemperature, "°C", temperatureTooltipCallback);

        // Implement the line chart in dashboard for the relative humidity
        if (graphHumidity) {
            graphHumidity.destroy();
        }
        var dataHumidity = createLineChartData("Relative Humidity", humidity, time);
        const humidityTooltipCallback = (tooltipItems) => tooltipItems.raw + " %";
        graphHumidity = createLineChartConfig(graphTargetHumidity, dataHumidity, "%", humidityTooltipCallback);

        // Implement the line chart in dashboard for the metabolic rate
        if (graphMetRate) {
            graphMetRate.destroy();
        }
        var dataMet = createLineChartData("Metabolic Rate", met, time);
        const metRateTooltipCallback = (tooltipItems) => tooltipItems.raw + " met";
        graphMetRate = createLineChartConfig(graphTargetMetabolic, dataMet, "met", metRateTooltipCallback);

        // Implement the line chart in dashboard for the VOC index
        if (graphVOC) {
            graphVOC.destroy();
        }
        var dataVOC = createLineChartData("VOC Index", voc_index, time);
        const vocTooltipCallback = (tooltipItems, data) => data.datasets[tooltipItems.datasetIndex].label + ': ' + tooltipItems.raw;
        graphVOC = createLineChartConfig(graphTargetVOC, dataVOC, "voc.", vocTooltipCallback);

        // ---------------------
        // END OF SECTION: IMPLEMENTATION OF THE DASHBOARD LINE CHARTS
        // ---------------------

        var canvases = document.getElementsByClassName("chart-calibration");
        var loadingTexts = document.getElementsByClassName("text-calibration");

        function showLoading() {
            // Apply the blur to each canvas element
            Array.from(canvases).forEach(canvas => {
                canvas.classList.add("blur");
            });

            // Display each loading text
            Array.from(loadingTexts).forEach(loadingText => {
                loadingText.style.display = "block";
            });
        }

        // Function to hide loading
        function hideLoading() {
            // Remove the blur from each canvas element
            Array.from(canvases).forEach(canvas => {
                canvas.classList.remove("blur");
            });

            // Hide each loading text
            Array.from(loadingTexts).forEach(loadingText => {
                loadingText.style.display = "none";
            });
        }

//        showLoading();

    });
}

updateDashboard();

setInterval(updateDashboard, 8000);
