function createLineChartConfigLEMPricing(graphTarget, data, yAxisUnit, tooltipLabelCallback) {
    return new Chart(graphTarget, {
        type: 'line',
        data: data,
        options: {
            animation: false,
            scales: {
                yAxes: [{
                    ticks: {
                        padding: 12,
                        fontFamily: "Josefin Sans",
                        suggestedMin: Math.min(...data.datasets[0].data),
                        suggestedMax: Math.max(...data.datasets[0].data),
                        beginAtZero: true,
                        autoSkip: true,
                        maxTicksLimit: 4,
                        callback: function(value) {
                            return value + " " + yAxisUnit;
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
                    label: tooltipLabelCallback
                }
            }
        }
    });
}

function updateDashboardPricing() {
    $.getJSON('/get_electricity_tariffs_dash', function (data) {


        console.log(data);

//        data.forEach(function(entry) {
//            prices.push(entry.price);
//            hours.push(entry.hour);
//        });


        const prices = Object.values(data);
        const hours = Object.keys(data).map(Number);

        console.log(prices);

        console.log(hours);

        var graphTargetLEMPricing = $("#session-lem-pricing");
        document.getElementById("latest-lem-price").innerHTML = prices.at(-1) + ' €';

        var dataLEM = createLineChartData("LEM", prices, hours);
        const energyPriceTooltipCallback = (tooltipItems) => tooltipItems.yLabel.toFixed(2) + " €" + " / Hour: " + tooltipItems.index + ":00";
        var graphLEM = createLineChartConfigLEMPricing(graphTargetLEMPricing, dataLEM, "€", energyPriceTooltipCallback);

    });
}

updateDashboardPricing();