let categorizedPowerPerHour = {};

function aggregatePower(category, hour, power) {
    if (!categorizedPowerPerHour[hour]) {
        categorizedPowerPerHour[hour] = {};
    }
    categorizedPowerPerHour[hour][category] = (categorizedPowerPerHour[hour][category] || 0) + power;
}

function formatHour(hour) {
    return `${hour.toString().padStart(2, '0')}:00`;
}

function aggregatePower(category, hour, power) {
    if (!categorizedPowerPerHour[hour]) {
        categorizedPowerPerHour[hour] = {};
    }
    categorizedPowerPerHour[hour][category] = (categorizedPowerPerHour[hour][category] || 0) + power;
}

function processOptimalSchedule(category, items, hasPrefix = false) {
    items.forEach(item => {
        const [hour, power] = hasPrefix ? item.slice(1) : item;
        aggregatePower(category, hour, power);
    });
}

processOptimalSchedule('AC', optimalSchedule["Air Conditioning Power and Temperature"]);
processOptimalSchedule('Electric Vehicle', optimalSchedule["Power Variable Loads"], true);
processOptimalSchedule('Electric Water Heater', optimalSchedule["Power Constant Loads"], true);

const applianceMap = {
    1: 'Washing Machine',
    2: 'Dish Washer',
    3: 'Tumble Dryer'
};

optimalSchedule["Time-Shiftable Loads"].forEach(item => {
    const [id, hour, duration] = item;
    const applianceName = applianceMap[id];
    for (let i = 0; i < duration; i++) {
        const currentHour = hour + i;
        aggregatePower(applianceName, currentHour, 1);
    }
});

const categories = ['AC', 'Electric Vehicle', 'Electric Water Heater', 'Washing Machine', 'Dish Washer', 'Tumble Dryer'];
const baseColors = {
    'AC': 'rgba(255, 99, 132,',
    'Electric Vehicle': 'rgba(54, 162, 235,',
    'Electric Water Heater': 'rgba(255, 206, 86,',
    'Washing Machine': 'rgba(153, 102, 255,',
    'Dish Washer': 'rgba(255, 159, 64,',
    'Tumble Dryer': 'rgba(75, 192, 192,'
};

const backgroundColors = {};
const borderColors = {};

Object.keys(baseColors).forEach(key => {
    backgroundColors[key] = `${baseColors[key]}0.2)`;
    borderColors[key] = `${baseColors[key]}1)`;
});

const datasets = categories.map(category => ({
    label: category,
    data: Object.keys(categorizedPowerPerHour).sort((a, b) => a - b).map(hour => categorizedPowerPerHour[hour][category] || 0),
    backgroundColor: backgroundColors[category],
    borderColor: borderColors[category],
    borderWidth: 1,
    stack: 'Stack 0'
}));

datasets.forEach(dataset => {
  dataset.yAxisID = dataset.label === 'Electricity Price ($/kWh)' ? 'y-axis-1' : 'y-axis-0';
});

const pricesDataset = {
    label: 'Electricity Price (€/kWh)',
    data: Object.keys(prices).map(hour => prices[hour]),
    borderColor: '#000000',
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    type: 'line',
    fill: false,
    yAxisID: 'y-axis-1',
    borderWidth: 1,
    pointRadius: 0,
};

const chartData1 = {
    labels: Object.keys(categorizedPowerPerHour).sort((a, b) => a - b).map(hour => formatHour(hour)),
    datasets: [...datasets, pricesDataset] // Correctly include all datasets in one array
};

var ctx1 = document.getElementById('powerConsumptionChart').getContext('2d');
var powerConsumptionChart = new Chart(ctx1, {
    type: 'bar',
    data: chartData1,
    options: {
        legend: {
            display: true,
            position: 'top',
            pointRadius: 20,
            labels: {
                fullWidth: true,
                usePointStyle: true,
                boxWidth: 10,
                pointStyle: 'rect',
            },
        },
        scales: {
            xAxes: [{
                gridLines: {
                    display: false
                },
                ticks: {
                    display: true,
                    callback: function(value, index, values) {
                        return value;
                    }
                }
            }],
            yAxes: [{
                type: 'linear',
                display: true,
                position: 'left',
                id: 'y-axis-0',
                gridLines: {
                    drawOnChartArea: false,
                },
                ticks: {
                    display: true,
                    suggestedMin: 0,
                    autoSkip: true,
                    maxTicksLimit: 4,
                    callback: function(value, index, values) {
                        return value + 'kW';
                    }
                }
            }, {
                type: 'linear',
                display: true,
                position: 'right',
                id: 'y-axis-1',
                gridLines: {
                    drawOnChartArea: false,
                },
                ticks: {
                    display: true,
                    suggestedMin: 0,
                    suggestedMax: 0.3,
                    autoSkip: true,
                    maxTicksLimit: 4,
                    callback: function(value, index, values) {
                        return value + '€/kWh';
                    }
                }
            }]
        },
        tooltips: {
            mode: 'index',
            intersect: false,
            callbacks: {
                label: function(tooltipItem, data) {
                    let label = data.datasets[tooltipItem.datasetIndex].label || '';
                    if (label) {
                        label += ': ';
                    }
                    label += tooltipItem.yLabel;
                    if (tooltipItem.datasetIndex !== data.datasets.length - 1) {
                        label += ' kW';
                    } else {
                        label += ' $/kWh';
                    }
                    return label;
                }
            }
        }
    }
});

const labels = Object.keys(operationData).map(label => {
    return label.split('_')
        .slice(0, 2)
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
});
const chartData = Object.values(operationData).map((time) => time);

const ctx = document.getElementById('operationChart').getContext('2d');
const operationChart = new Chart(ctx, {
    type: 'horizontalBar',
    data: {
        labels: labels.map(label => label.replace('_', ' ')),
        datasets: [{
            label: 'Operation Time',
            data: chartData,
            backgroundColor: 'rgba(130, 223, 103, 0.8)',
        }]
    },
    options: {
        scales: {
            yAxes: [{
                ticks: {
                    fontFamily: "Josefin Sans",
                    beginAtZero: true,
                    autoSkip: false,
                }
            }],
            xAxes: [{
                gridLines: {
                    display: true,
                    drawOnChartArea: true
                },
                ticks: {
                    suggestedMin: 0,
                    suggestedMax: 7,
                    beginAtZero: false,
                    autoSkip: false,
                    maxTicksLimit: 24,
                }
            }],
        },
        legend: {
            display: false
        },
        tooltips: {
            callbacks: {
                label: function(tooltipItem, data) {
                    const label = data.labels[tooltipItem.index];
                    const [startTime, endTime] = Object.values(operationData)[tooltipItem.index];
                    return `Earliest Start: ${startTime}:00 - Latest Finish: ${endTime}:00`;
                }
            }
        }
    }
});