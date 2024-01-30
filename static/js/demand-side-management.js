let categorizedPowerPerHour = {};

function aggregatePower(category, hour, power) {
  if (!categorizedPowerPerHour[hour]) {
    categorizedPowerPerHour[hour] = {};
  }
  categorizedPowerPerHour[hour][category] = (categorizedPowerPerHour[hour][category] || 0) + power;
}

optimalSchedule["Air Conditioning Power and Temperature"].forEach(item => {
  const [hour, power] = item;
  aggregatePower('AC', hour, power);
});

optimalSchedule["Power Variable Loads"].forEach(item => {
  const [, hour, power] = item;
  aggregatePower('Electric Vehicle', hour, power);
});

optimalSchedule["Power Constant Loads"].forEach(item => {
  const [, hour, power] = item;
  aggregatePower('Electric Water Heater', hour, power);
});

const applianceMap = {
  1: 'Washing Machine',
  2: 'Dish Washer',
  3: 'Tumble Dryer'
};

function aggregatePower(category, hour, power) {
  if (!categorizedPowerPerHour[hour]) {
    categorizedPowerPerHour[hour] = {};
  }
  categorizedPowerPerHour[hour][category] = (categorizedPowerPerHour[hour][category] || 0) + power;
}

optimalSchedule["Time-Shiftable Loads"].forEach(item => {
  const [id, hour, duration] = item;
  const applianceName = applianceMap[id];
  for (let i = 0; i < duration; i++) {
    const currentHour = hour + i;
    aggregatePower(applianceName, currentHour, 1);
  }
});

const categories = ['AC', 'Electric Vehicle', 'Electric Water Heater', 'Washing Machine', 'Dish Washer', 'Tumble Dryer'];
const colors = {
  'AC': 'rgba(255, 99, 132, 0.2)',
  'Electric Vehicle': 'rgba(54, 162, 235, 0.2)',
  'Electric Water Heater': 'rgba(255, 206, 86, 0.2)',
  'Washing Machine': 'rgba(153, 102, 255, 0.2)',
  'Dish Washer': 'rgba(255, 159, 64, 0.2)',
  'Tumble Dryer': 'rgba(75, 192, 192, 0.2)'
};
const borderColors = {
  'AC': 'rgba(255,99,132,1)',
  'Electric Vehicle': 'rgba(54, 162, 235, 1)',
  'Electric Water Heater': 'rgba(255, 206, 86, 1)',
  'Washing Machine': 'rgba(153, 102, 255, 1)',
  'Dish Washer': 'rgba(255, 159, 64, 1)',
  'Tumble Dryer': 'rgba(75, 192, 192, 1)'
};

const datasets = categories.map(category => ({
  label: category,
  data: Object.keys(categorizedPowerPerHour).sort((a, b) => a - b).map(hour => categorizedPowerPerHour[hour][category] || 0),
  backgroundColor: colors[category],
  borderColor: borderColors[category],
  borderWidth: 1,
  stack: 'Stack 0'
}));

function formatHour(hour) {
  return `${hour.toString().padStart(2, '0')}:00`;
}

datasets.forEach(dataset => {
  // Assuming the last dataset is for prices
  if (dataset.label === 'Electricity Price ($/kWh)') {
    dataset.yAxisID = 'y-axis-1';
  } else {
    dataset.yAxisID = 'y-axis-0';
  }
});

// Adding the prices dataset
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
    display: true, // Ensure this is set to true
    position: 'top', // Optional: can adjust based on where you want the legend
    // Additional customization options for the legend can go here
  },
  scales: {
    xAxes: [{ // Configuration for the x-axis
      gridLines: {
        display: false
      },
      ticks: {
        display: true, // Change this to true to display x-axis labels
        callback: function(value, index, values) {
          return value; // Or any custom formatting
        }
      }
    }],
    yAxes: [{ // Primary y-axis for the bar chart
      type: 'linear',
      display: true,
      position: 'left',
      id: 'y-axis-0',
    }, {
      type: 'linear',
      display: true,
      position: 'right',
      id: 'y-axis-1',
      gridLines: {
        drawOnChartArea: false, // Only display the grid for the primary y-axis
      },
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
        if (tooltipItem.datasetIndex !== data.datasets.length - 1) { // Assuming the last dataset is your line chart
          label += ' kW'; // Add kW for bar charts
        } else {
          label += ' $/kWh'; // Add $/kWh for the line chart
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
                    return `Early Start: ${startTime}:00 - Late Start: ${endTime}:00`;
                }
            }
        }
    }
});
