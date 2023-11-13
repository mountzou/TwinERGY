function getConsumerPreferences() {
    $.getJSON('/get_data_preferences', function (data) {

        // Get the preferences related to the thermal comfort tolerance [min, max values]
        var thermal_comfort_max = data['preferences'][0]['thermal_comfort_preferences']['thermal_comfort_max'];
        var thermal_comfort_min = data['preferences'][0]['thermal_comfort_preferences']['thermal_comfort_min'];

        // Get the preferences related to the thermal comfort tolerance [min, max values]
        var temperature_max = data['preferences'][0]['temperature_preferences']['temperature_max'];
        var temperature_min = data['preferences'][0]['temperature_preferences']['temperature_min'];

        // Get the preferences related to the importance of residential flexible loads
        var appliances = ['electric_vehicle', 'washing_machine', 'tumble_drier', 'water_heater', 'dish_washer'];
        var importanceValues = {};

        appliances.forEach(function(appliance) {
            importanceValues[appliance] = data['preferences'][0]['flexible_load_preferences']['importance_' + appliance];
        });

        // Get the preferences related to the desired operation time window of each load
        var from_electric_vehicle = data['preferences'][0]['electric_vehicle_time']['electric_vehicle_time_from'];
        var to_electric_vehicle = data['preferences'][0]['electric_vehicle_time']['electric_vehicle_time_to'];
        var from_washing_machine = data['preferences'][0]['washing_machine_time']['washing_machine_time_from'];
        var to_washing_machine = data['preferences'][0]['washing_machine_time']['washing_machine_time_to'];
        var from_tumble_drier = data['preferences'][0]['tumble_drier_time']['tumble_drier_time_from'];
        var to_tumble_drier = data['preferences'][0]['tumble_drier_time']['tumble_drier_time_to'];
        var from_water_heater = data['preferences'][0]['water_heater_time']['water_heater_time_from'];
        var to_water_heater = data['preferences'][0]['water_heater_time']['water_heater_time_to'];
        var from_dish_washer = data['preferences'][0]['dish_washer_time']['dish_washer_time_from'];
        var to_dish_washer = data['preferences'][0]['dish_washer_time']['dish_washer_time_to'];

        $("#preference_thermal_comfort").ionRangeSlider({
          grid: !0,
          type: 'double',
          from: thermal_comfort_min+3,
          to: thermal_comfort_max+3,
          values: ["Cold", "Cool", "Slightly Cool", "Neutral", "Slightly Warm", "Warm", "Hot"],
          onChange: function(data) {
            var fromValue = data.from - 3;
            var toValue = data.to - 3;
              $.ajax({
                url: '/update_preferences_thermal_comfort',
                type: 'POST',
                data: {
                  user_thermal_level_min: fromValue,
                  user_thermal_level_max: toValue
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                },
                error: function(response) {
                  console.log("Error updating preferences");
                }
              });
          },
        });

        $("#preference_indoor_temperature").ionRangeSlider({
          grid: !0,
          type: 'double',
          from: temperature_min - 16,
          to: temperature_max - 16,
          values: ["16 °C", "17 °C", "18 °C", "19 °C", "20 °C", "21 °C", "22 °C", "23 °C"],
          onChange: function(data) {
            var fromValue = data.from + 16;
            var toValue = data.to + 16;
            console.log("New values: " + fromValue + ", " + toValue);
              $.ajax({
                url: '/update_preferences_temperature',
                type: 'POST',
                data: {
                  user_temp_min: fromValue,
                  user_temp_max: toValue
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                },
                error: function(response) {
                  console.log("Error updating preferences");
                }
              });
          },
        });

        function updateAppliancePreference(appliance, fromValue) {
            $.ajax({
                url: `/update/${appliance}/preference`,
                type: 'POST',
                data: {
                    [`importance_${appliance}`]: fromValue
                },
                success: function(response) {
                    console.log(`${appliance} preferences updated successfully`);
                },
                error: function(xhr, status, error) {
                    console.log(`Error updating ${appliance} preferences: ${error}`);
                }
            });
        }

        function initializePreferenceSlider(appliance, initialValue) {
            $(`#preference_${appliance}`).ionRangeSlider({
                grid: true,
                min: 0,
                max: 5,
                from: initialValue,
                values: ["Not Important", "Slightly Important", "Important", "Fairly Important", "Very Important"],
                onChange: function(data) {
                    updateAppliancePreference(appliance, data.from);
                }
            });
        }

        appliances.forEach(function(appliance) {
            initializePreferenceSlider(appliance, importanceValues[appliance]);
        });


        function initializeTimeRangeSlider(appliance, fromValue, toValue) {
            $(`#preference_range_${appliance}`).ionRangeSlider({
                grid: true,
                type: 'double',
                from: fromValue,
                to: toValue,
                values: hoursList,
                onChange: function(data) {
                    $.ajax({
                        url: `/update/${appliance}/time_range`,
                        type: 'POST',
                        data: {
                            [`from${capitalizeFirstLetter(appliance)}`]: data.from,
                            [`to${capitalizeFirstLetter(appliance)}`]: data.to,
                        },
                        success: function(response) {
                            console.log(`${appliance} time range updated successfully`);
                        },
                        error: function(response) {
                            console.log(`Error updating ${appliance} time range`);
                        }
                    });
                }
            });
        }

    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    let hoursList = [];
    for (let hour = 0; hour < 24; hour++) {
        let hourString = hour < 10 ? '0' + hour : '' + hour;
        hoursList.push(hourString + ':00');
    }

    var timeRangeValues = {
        'electric_vehicle': { from: from_electric_vehicle, to: to_electric_vehicle },
        'washing_machine': { from: from_washing_machine, to: to_washing_machine },
        'dish_washer': { from: from_dish_washer, to: to_dish_washer },
        'tumble_drier': { from: from_tumble_drier, to: to_tumble_drier },
        'water_heater': { from: from_water_heater, to: to_water_heater }
    };

    appliances.forEach(function(appliance) {
        var range = timeRangeValues[appliance];
        initializeTimeRangeSlider(appliance, range.from, range.to);
    });

})};

function getLoadWeights() {
    $.getJSON('/get_preferences_weights', function (data) {
        appliances.forEach(function(appliance) {
        console.log(data[appliance.name])
            const weight = data[appliance.name].shift();

            const progressBar = document.getElementById(`weight-${appliance.id}`);
            progressBar.style.width = weight + '%';
            progressBar.setAttribute('aria-valuenow', weight);

            const weightPercentageLabel = document.getElementById(`weight-per-${appliance.id}`);
            weightPercentageLabel.innerHTML = weight + '%';
        });

    });
}

getConsumerPreferences();

getLoadWeights();
