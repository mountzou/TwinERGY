var graphTemperature, graphHumidity, graphMetRate, graphVOC, graphPMV;

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
            element.innerHTML = 'Latest update at ' + latestTime;;
        });

        var graphTargetTemperature = $("#session-temperature");
        var graphTargetHumidity = $("#session-humidity");
        var graphTargetMetabolic = $("#session-metabolic");
        var graphTargetPMV = $("#session-thermal-comfort");
        var graphTargetVOC = $("#session-VOC");

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

        // Create the chart data
        var dataThermalComfort = createLineChartData("Thermal Comfort", numericalData, time);
        const thermalComfortTooltipCallback = (tooltipItems) => fangerScaleCategories[tooltipItems.yLabel - 1];

        // Destroy the old chart if it exists
        if (graphPMV) {
            graphPMV.destroy();
        }
        // Create the chart
        graphPMV = createLineChartConfigPMV(graphTargetPMV, dataThermalComfort, fangerScaleCategories, thermalComfortTooltipCallback);

        // Implement the line chart in dashboard for the air temperature
        var dataTemperature = createLineChartData("Air Temperature", temperature, time);
        const temperatureTooltipCallback = (tooltipItems) => tooltipItems.yLabel.toFixed(2) + " °C";

        // Destroy the old chart if it exists
        if (graphTemperature) {
            graphTemperature.destroy();
        }
        var graphTemperature = createLineChartConfig(graphTargetTemperature, dataTemperature, "°C", temperatureTooltipCallback);

        // Implement the line chart in dashboard for the relative humidity
        var dataHumidity = createLineChartData("Relative Humidity", humidity, time);
        const humidityTooltipCallback = (tooltipItems) => tooltipItems.yLabel + " %";

        // Destroy the old chart if it exists
        if (graphHumidity) {
            graphHumidity.destroy();
        }
        var graphHumidity = createLineChartConfig(graphTargetHumidity, dataHumidity, "%", humidityTooltipCallback);

        // Implement the line chart in dashboard for the metabolic rate
        var dataMet = createLineChartData("Metabolic Rate", met, time);
        const metRateTooltipCallback = (tooltipItems) => tooltipItems.yLabel + " met";

        // Destroy the old chart if it exists
        if (graphMetRate) {
            graphMetRate.destroy();
        }
        var graphMetRate = createLineChartConfig(graphTargetMetabolic, dataMet, "met", metRateTooltipCallback);

        // Implement the line chart in dashboard for the VOC index
        var dataVOC = createLineChartData("VOC Index", voc_index, time);
        const vocTooltipCallback = (tooltipItems, data) => data.datasets[tooltipItems.datasetIndex].label + ': ' + tooltipItems.yLabel;

        // Destroy the old chart if it exists
        if (graphVOC) {
            graphVOC.destroy();
        }
        var graphVOC = createLineChartConfig(graphTargetVOC, dataVOC, "voc.", vocTooltipCallback);

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
