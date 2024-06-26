// A function that convert the PMV index to percentage for the donut chart of dashboard
function convertPMVToPercentage(value) {
  var percentage = (1 - Math.abs(value) / 3) * 100;
  return percentage.toFixed(2);
}

// A function that replaces the '/' with '-' in date formatted variables
function replaceDateFormat(inputString) {
    return inputString.split('/').join('-');
}

// A function that converts the timestamp to human readable form
function unixToHumanReadable(unixTimestamp) {
    let date = new Date(unixTimestamp * 1000);
    return date.toLocaleString();
}

// A function that converts the timestamp to human readable form without the time
function unixToHumanReadableWithoutTime(unixTimestamp) {
    let date = new Date(unixTimestamp * 1000);
    let options = { month: 'long', day: 'numeric' };
    return date.toLocaleDateString('en-US', options);
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

// A function that implements the Yaxis callback for thermal comfort
function thermalComfortYAxisCallback(value) {
    switch (value) {
        case -3:
            return 'Cold';
        case -2:
            return 'Cool';
        case -1:
            return 'Slightly Cool';
        case 0:
            return 'Neutral';
        case 1:
            return 'Slightly Warm';
        case 2:
            return 'Warm';
        case 3:
            return 'Hot';
        default:
            return '';
    }
}

// A function that updates the innerHTML content of an HTML element by element ID
function updateElement(id, content) {
    document.getElementById(id).innerHTML = content;
}

// A function that updates the innerHTML content of an HTML element by class name
function updateElementsByClass(className, content) {
    let elements = document.getElementsByClassName(className);
    for (let i = 0; i < elements.length; i++) {
        elements[i].innerHTML = content;
    }
}

// A function that generates the chart configuration object
function createChartConfig(labels, data, datasetLabel) {
    return {
        labels: labels,
        datasets: [{
            label: datasetLabel,
            type: "line",
            borderColor: "rgb(255, 186, 77)",
            backgroundColor: "rgba(255, 186, 77, .1)",
            borderWidth: 3,
            data: data,
            fill: true
        }]
    };
}

// A function that generates a new Chart instance with the given parameters
function createChart(target, data, yAxisCallback, yAxisMin, yAxisMax, customTooltips, yAxisStepSize, annotationsConfig) {
    return new Chart(target, {
        type: 'line',
        data: data,
        options: {
            annotation:annotationsConfig,
            animation: false,
            scales: {
                yAxes: [{
                    ticks: {
                        padding: 25,
                        fontFamily: "Josefin Sans",
                        beginAtZero: false,
                        autoSkip: true,
                        maxTicksLimit: 7,
                        callback: yAxisCallback,
                        ...(yAxisMin ? { min: yAxisMin } : {}),
                        ...(yAxisMax ? { max: yAxisMax } : {}),
                        ...(yAxisStepSize ? { stepSize: yAxisStepSize } : {})
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
            ...(customTooltips ? { tooltips: customTooltips } : {})
        }
    });
}

var currentStartDate = moment().subtract(1, 'day').format('YYYY/MM/DD');
var currentEndDate = moment().format('YYYY/MM/DD');

function updateThermalComfort(start_date, end_date) {
    $.getJSON('/get_data_thermal_comfort_range', {'start_date': start_date, 'end_date': end_date}, function (data) {
        let temperature = data.map(x => x[0]);
        let humidity = data.map(x => x[1]);
        let time = data.map(x => unixToHumanReadable(x[2]));
        let timee = data.map(x => x[2]);
        let met = data.map(x => x[4]);
        let pmv = data.map(x => x[5]);
        console.log(pmv);
        let pmvStatus= pmv.map(get_pmv_status);

        let latestTemperature = temperature[temperature.length - 1];
        let latestHumidity = humidity[humidity.length - 1];
        let latestTime = time[time.length - 1];
        let latestMet = met[met.length - 1]
        let latestThermalComfort = pmv[pmv.length - 1]

        // Update the innerHTML content of HTML elements regarding the latest data
        const noData = 'Data unavailable for the selected range';
        const latestTemperatureContent = latestTemperature === undefined ? noData : latestTemperature + ' °C';
        const latestHumidityContent = latestHumidity === undefined ? noData : latestHumidity + ' %';
        const latestMetContent = latestMet === undefined ? noData : latestMet + ' met';
        const latestThermalComfortContent = latestThermalComfort === undefined ? noData : get_pmv_status(latestThermalComfort);

        updateElement("latest-indoor-temperature", latestTemperatureContent);
        updateElement("latest-indoor-humidity", latestHumidityContent);
        updateElement("latest-met", latestMetContent);
        updateElement("latest-thermal-comfort", latestThermalComfortContent);

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

        // Update the mean air temperature, relative humidity and metabolic rate
        const noDataValue = '-';
        const dailyMeanTemperatureContent = latestTemperature === undefined ? noDataValue : mean_temp + ' °C';
        const dailyMeanHumidityContent = latestTemperature === undefined ? noDataValue : mean_hum + ' %';
        const dailyMeanMetContent = latestTemperature === undefined ? noDataValue : mean_met + ' met';

        updateElement("daily-mean-temperature", dailyMeanTemperatureContent);
        updateElement("daily-mean-humidity", dailyMeanHumidityContent);
        updateElement("daily-mean-met", dailyMeanMetContent);

        // Select all elements with the class "l-updated"
        const latestTimeContent = latestTemperature === undefined ? noDataValue : 'Latest update at ' + latestTime;

        updateElementsByClass("l-updated", latestTimeContent);

        var graphTargetAirTemperature = $("#chart-temperature");
        var graphTargetHumidity = $("#chart-humidity");
        var graphTargetMetabolic = $("#chart-met");
        var graphTargetThermalComfort = $("#chart-thermal-comfort");

        var indoorTemperature = createChartConfig(time, temperature, "Air Temperature");
        var indoorHumidity = createChartConfig(timee, humidity, "Relative Humidity");
        var indoorMetabolic = createChartConfig(time, met, "Metabolic Rate");
        var thermalComfort = createChartConfig(time, pmv, "Thermal Comfort");

        var thermalComfortTooltips = {
            enabled: false,
            mode: 'single',
            callbacks: {
                label: function(tooltipItems, data) {
                    return 'Thermal Comfort: ' + get_pmv_status(tooltipItems.yLabel);
                },
            }
        };

        var yAxisMin = -3;
        var yAxisMax = 3;
        var numberOfTicks = 7;
        var yAxisStepSize = 1;

        var graphThermalComfort = createChart(
            graphTargetThermalComfort,
            thermalComfort,
            thermalComfortYAxisCallback,
            yAxisMin,
            yAxisMax,
            thermalComfortTooltips,
            yAxisStepSize
        );

        let annotationsConfig = {
            annotations: []
        };

        let labelCounter = 0;

        for (let i = 0; i < timee.length - 1; i++) {
            if (new Date(timee[i] * 1000).getUTCDate() !== new Date(timee[i + 1] * 1000).getUTCDate()) {
                annotationsConfig.annotations.push({
                    type: 'line',
                    mode: 'vertical',
                    scaleID: 'x-axis-0',
                    value: i + 0.5,
                    borderColor: '#1e2727',
                    borderWidth: 1,
                    borderDash: [2, 2],
                    label: {
                        fontFamily: "Josefin Sans",
                        fontSize: 13,
                        fontStyle: "normal",
                        fontColor: "#1e2727",
                        content: 'End of '+unixToHumanReadableWithoutTime(timee[i]),
                        enabled: true,
                        position: (labelCounter % 2 === 0) ? 'top' : 'bottom',
                        backgroundColor: 'rgba(0, 0, 0, 0)',
                    },
                });
                labelCounter++;
            }
        }

        var graphTemperature = createChart(graphTargetAirTemperature, indoorTemperature, (value) => value + " °C", false, null, null, null, annotationsConfig);
        var graphMetabolic = createChart(graphTargetMetabolic, indoorMetabolic, (value) => value + " met", false, null, null, null, annotationsConfig);
        var graphHumidity = createChart(graphTargetHumidity, indoorHumidity, (value) => value + " %", false, null, null, null, annotationsConfig);

    });
}

function initDateRangePicker() {
    localStorage.removeItem('startDate');
    localStorage.removeItem('endDate');
    // Calculate the default start and end dates for the latest 24 hours
    var defaultEndDate = moment().format('YYYY/MM/DD');
    var defaultStartDate = moment().subtract(1, 'day').format('YYYY/MM/DD');

    // Get the stored date range values or use the default ones
    var storedStartDate = localStorage.getItem('startDate') || defaultStartDate;
    var storedEndDate = localStorage.getItem('endDate') || defaultEndDate;

    $('#thermalComfortRange').daterangepicker({
        drops: 'down',
        startDate: defaultStartDate,
        endDate: defaultEndDate,
        maxDate: moment().format('YYYY/MM/DD'),
        locale: {
            format: 'YYYY/MM/DD'
        },
        autoUpdateInput: false,
        applyButtonClasses: 'btn-primary'
    });

    $('#thermalComfortRange').val(storedStartDate + ' / ' + storedEndDate);

    $('#thermalComfortRange').on('apply.daterangepicker', function(ev, picker) {

        var startDate = picker.startDate.format('YYYY/MM/DD');
        var endDate = picker.endDate.format('YYYY/MM/DD');

        $(this).val(startDate + ' / ' + endDate);

        localStorage.setItem('startDate', startDate);
        localStorage.setItem('endDate', endDate);

        var formattedStartDate = replaceDateFormat(startDate)
        var formattedEndDate = replaceDateFormat(endDate)

        updateThermalComfort(formattedStartDate, formattedEndDate);
    });
}

initDateRangePicker();

localStorage.setItem('startDate', currentStartDate);
localStorage.setItem('endDate', currentEndDate);

currentStartDate = replaceDateFormat(currentStartDate);
currentEndDate = replaceDateFormat(currentEndDate);
updateThermalComfort(currentStartDate, currentEndDate);

setInterval(function() {
  var applystartDate_ = localStorage.getItem('startDate');
  var applyendDate_ = localStorage.getItem('endDate');

  if(applyendDate_===moment().format('YYYY/MM/DD')){
    var formattedStartDate_ = replaceDateFormat(applystartDate_)
    var formattedEndDate_ = replaceDateFormat(applyendDate_)
    updateThermalComfort(formattedStartDate_, formattedEndDate_);
  }

}, 8000);
