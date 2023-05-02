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

var startDate = moment().subtract(1, 'day').format('YYYY/MM/DD');
var endDate = moment().format('YYYY/MM/DD');

var currentStartDate = startDate;
var currentEndDate = endDate;

function updateThermalComfort(start_date, end_date) {
    $.getJSON('/get_data_thermal_comfort_range', {'start_date': start_date, 'end_date': end_date}, function (data) {
        let temperature = data.map(x => x[0]);
        let humidity = data.map(x => x[1]);
        let time = data.map(x => unixToHumanReadable(x[2]));
        let met = data.map(x => x[4]);
        let pmv = data.map(x => x[5]);
        let pmvStatus= pmv.map(get_pmv_status);

        let latestTemperature = temperature[temperature.length - 1];
        let latestHumidity = humidity[humidity.length - 1];
        let latestTime = time[time.length - 1];
        let latestMet = met[met.length - 1]
        let latestThermalComfort = pmv[pmv.length - 1]

        // Update the latest temperature and humidity
        // Handle empty data
        if (latestTemperature===undefined){
            document.getElementById("latest-indoor-temperature").innerHTML = 'No available data for the selected time range';
            document.getElementById("latest-indoor-humidity").innerHTML = 'No available data for the selected time range';
            document.getElementById("latest-met").innerHTML = 'No available data for the selected time range';
            document.getElementById("latest-thermal-comfort").innerHTML = 'No available data for the selected time range';
        }
        else{
            document.getElementById("latest-indoor-temperature").innerHTML = latestTemperature + ' °C';
            document.getElementById("latest-indoor-humidity").innerHTML = latestHumidity + ' %';
            document.getElementById("latest-met").innerHTML = latestMet + ' met';
            document.getElementById("latest-thermal-comfort").innerHTML = get_pmv_status(latestThermalComfort) ;
        }

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
        if (latestTemperature===undefined){
            document.getElementById("daily-mean-temperature").innerHTML ='- °C';
            document.getElementById("daily-mean-humidity").innerHTML = '- %';
            document.getElementById("daily-mean-met").innerHTML = '- met';
        }
        else{
            document.getElementById("daily-mean-temperature").innerHTML = mean_temp+' °C';
            document.getElementById("daily-mean-humidity").innerHTML = mean_hum+' %';
            document.getElementById("daily-mean-met").innerHTML = mean_met+' met';
        }
        // Select all elements with the class "l-updated"
        let time_elements = document.getElementsByClassName("l-updated");

        if (latestTemperature===undefined){
            for (let i = 0; i < time_elements.length; i++) {
                time_elements[i].innerHTML = '     ';
            }
        }
        else{
            for (let i = 0; i < time_elements.length; i++) {
                time_elements[i].innerHTML = 'Latest update at '+latestTime;
            }
        }

        var graphTargetAirTemperature = $("#chart-temperature");
        var graphTargetHumidity = $("#chart-humidity");
        var graphTargetMetabolic = $("#chart-met");
        var graphTargetThermalComfort = $("#chart-thermal-comfort");

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
                borderWidth: 2,
                data: met,
                fill: true
            }]
        };

        const pointBackgroundColors = pmv.map((value) => (value > 0 ? '#FF6D60' : '#088395'));

        var thermalComfort = {
            labels: time,
            datasets: [{
                label: "Thermal Comfort",
                type: "line",
                borderColor: "rgb(255, 186, 77)",
                backgroundColor: "rgb(255, 186, 77, .1)",
                borderWidth: 2,
                data: pmv,
                pointBackgroundColor: pointBackgroundColors,
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

        var graphThermalComfort = new Chart(graphTargetThermalComfort, {
            type: 'line',
            data: thermalComfort,
            options: {
                animation: false,
                scales: {
                    yAxes: [{
                        ticks: {
                            padding: 25,
                            fontFamily: "Josefin Sans",
                            beginAtZero: false,
                            min: -3,
                            max: 3,
                            callback: function (value, index, values) {
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
                    mode: 'single',
                    callbacks: {
                      label: function(tooltipItems, data) {
                        return 'Thermal Comfort: ' + get_pmv_status(tooltipItems.yLabel);
                      },
                    }
                },
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

function initDateRangePicker() {
    localStorage.removeItem('startDate');
    localStorage.removeItem('endDate');
    // Calculate the default start and end dates for the latest 24 hours
    var defaultEndDate = moment().format('YYYY/MM/DD');
    var defaultStartDate = moment().subtract(1, 'day').format('YYYY/MM/DD');

    // Get the stored date range values or use the default ones
    var storedStartDate = localStorage.getItem('startDate') || defaultStartDate;
    var storedEndDate = localStorage.getItem('endDate') || defaultEndDate;
    console.log(storedStartDate)
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

        var formattedStartDate = startDate.replace(/\//g, '-');
        var formattedEndDate = endDate.replace(/\//g, '-');
        updateThermalComfort(formattedStartDate, formattedEndDate);
    });
}

initDateRangePicker();

localStorage.setItem('startDate', currentStartDate);
localStorage.setItem('endDate', currentEndDate);
currentStartDate = currentStartDate.replace(/\//g, '-');
currentEndDate = currentEndDate.replace(/\//g, '-');
updateThermalComfort(currentStartDate, currentEndDate);

setInterval(function() {
//do not update if the range excludes the current day
  var applystartDate_ = localStorage.getItem('startDate');
  var applyendDate_ = localStorage.getItem('endDate');
  if(applyendDate_===moment().format('YYYY/MM/DD')){
    var formattedStartDate_ = applystartDate_.replace(/\//g, '-');
  var formattedEndDate_ = applyendDate_.replace(/\//g, '-');
  console.log(formattedEndDate_);
  updateThermalComfort(formattedStartDate_, formattedEndDate_);
}}, 8000);
