function getConsumerPreferences() {
    $.getJSON('/get_data_preferences', function (data) {

        // Get the preferences related to the thermal comfort tolerance [min, max values]
        var thermal_comfort_max = data['preferences'][0]['thermal_comfort_preferences']['thermal_comfort_max'];
        var thermal_comfort_min = data['preferences'][0]['thermal_comfort_preferences']['thermal_comfort_min'];

        // Get the preferences related to the thermal comfort tolerance [min, max values]
        var temperature_max = data['preferences'][0]['temperature_preferences']['temperature_max'];
        var temperature_min = data['preferences'][0]['temperature_preferences']['temperature_min'];

        // Get the preferences related to the importance of residential flexible loads
        var importance_electric_vehicle = data['preferences'][0]['flexible_load_preferences']['importance_electric_vehicle'];
        var importance_washing_machine = data['preferences'][0]['flexible_load_preferences']['importance_washing_machine'];
        var importance_tumble_drier = data['preferences'][0]['flexible_load_preferences']['importance_tumble_drier'];
        var importance_water_heater = data['preferences'][0]['flexible_load_preferences']['importance_water_heater'];
        var importance_dish_washer = data['preferences'][0]['flexible_load_preferences']['importance_dish_washer'];

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
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
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
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        $("#preference_electric_vehicle").ionRangeSlider({
          grid: !0,
          min: 0,
          max: 5,
          from: importance_electric_vehicle,
          values: ["Not Important", "Slightly Important", "Important", "Fairly Important", "Very Important"],
          onChange: function(data) {
            var fromValue = data.from;
            console.log("New values: " + fromValue);
              $.ajax({
                url: '/update_preferences_importance_electric_vehicle',
                type: 'POST',
                data: {
                  importance_electric_vehicle: fromValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        $("#preference_washing_machine").ionRangeSlider({
          grid: !0,
          min: 0,
          max: 5,
          from: importance_washing_machine,
          values: ["Not Important", "Slightly Important", "Important", "Fairly Important", "Very Important"],
          onChange: function(data) {
            var fromValue = data.from;
            console.log("New values: " + fromValue);
              $.ajax({
                url: '/update_preferences_importance_washing_machine',
                type: 'POST',
                data: {
                  importance_washing_machine: fromValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        $("#preference_dish_washer").ionRangeSlider({
          grid: !0,
          min: 0,
          max: 5,
          from: importance_dish_washer,
          values: ["Not Important", "Slightly Important", "Important", "Fairly Important", "Very Important"],
          onChange: function(data) {
            var fromValue = data.from;
              $.ajax({
                url: '/update_preferences_importance_dish_washer',
                type: 'POST',
                data: {
                  importance_dish_washer: fromValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        $("#preference_water_heater").ionRangeSlider({
          grid: !0,
          min: 0,
          max: 5,
          from: importance_water_heater,
          values: ["Not Important", "Slightly Important", "Important", "Fairly Important", "Very Important"],
          onChange: function(data) {
            var fromValue = data.from;
              $.ajax({
                url: '/update_preferences_importance_water_heater',
                type: 'POST',
                data: {
                  importance_water_heater: fromValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        $("#preference_tumble_drier").ionRangeSlider({
          grid: !0,
          min: 0,
          max: 5,
          from: importance_tumble_drier,
          values: ["Not Important", "Slightly Important", "Important", "Fairly Important", "Very Important"],
          onChange: function(data) {
            var fromValue = data.from;
              $.ajax({
                url: '/update_preferences_importance_tumble_drier',
                type: 'POST',
                data: {
                  importance_tumble_drier: fromValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        let hoursList = [];

        for (let hour = 0; hour < 24; hour++) {
          let hourString = hour < 10 ? '0' + hour : '' + hour;
          hoursList.push(hourString + ':00');
        }

        $("#preference_range_electric_vehicle").ionRangeSlider({
          grid: !0,
          type: 'double',
          from: from_electric_vehicle,
          to: to_electric_vehicle,
          values: hoursList,
          onChange: function(data) {
            var fromValue = data.from;
            var toValue = data.to;
              $.ajax({
                url: '/update_range_electric_vehicle',
                type: 'POST',
                data: {
                    fromElectricVehicle: fromValue,
                    toElectricVehicle: toValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        $("#preference_range_washing_machine").ionRangeSlider({
          grid: !0,
          type: 'double',
          from: from_washing_machine,
          to: to_washing_machine,
          values: hoursList,
          onChange: function(data) {
            var fromValue = data.from;
            var toValue = data.to;
              $.ajax({
                url: '/update_range_washing_machine',
                type: 'POST',
                data: {
                    fromWashingMachine: fromValue,
                    toWashingMachine: toValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        $("#preference_range_dish_washer").ionRangeSlider({
          grid: !0,
          type: 'double',
          from: from_dish_washer,
          to: to_dish_washer,
          values: hoursList,
          onChange: function(data) {
            var fromValue = data.from;
            var toValue = data.to;
              $.ajax({
                url: '/update_range_dish_washer',
                type: 'POST',
                data: {
                    fromDishWasher: fromValue,
                    toDishWasher: toValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        $("#preference_range_drier").ionRangeSlider({
          grid: !0,
          type: 'double',
          from: from_tumble_drier,
          to: to_tumble_drier,
          values: hoursList,
          onChange: function(data) {
            var fromValue = data.from;
            var toValue = data.to;
              $.ajax({
                url: '/update_range_tumble_drier',
                type: 'POST',
                data: {
                    fromTumbleDrier: fromValue,
                    toTumbleDrier: toValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

        $("#preference_range_water_heater").ionRangeSlider({
          grid: !0,
          type: 'double',
          from: from_water_heater,
          to: to_water_heater,
          values: hoursList,
          onChange: function(data) {
            var fromValue = data.from;
            var toValue = data.to;
              $.ajax({
                url: '/update_range_water_heater',
                type: 'POST',
                data: {
                    fromWaterHeater: fromValue,
                    toWaterHeater: toValue,
                },
                success: function(response) {
                  console.log("Preferences updated successfully");
                  // You can add any success handling code here
                },
                error: function(response) {
                  console.log("Error updating preferences");
                  // You can add any error handling code here
                }
              });
          },
        });

    });

}

function getLoadWeights() {
    $.getJSON('/get_preferences_weights', function (data) {
        weightElectricVehicle = data['Electric Vehicle'].shift()
        const progressBarEV = document.getElementById('weight-ev');
        progressBarEV.style.width = weightElectricVehicle + '%';
        progressBarEV.setAttribute('aria-valuenow', weightElectricVehicle);
        const weightPercentageEV = document.getElementById('weight-ev');
        weightPercentageEV.innerHTML = weightElectricVehicle + '%';

        weightWashingMachine = data['Washing Machine'].shift()
        const progressBarWM = document.getElementById('weight-wm');
        progressBarWM.style.width = weightWashingMachine + '%';
        progressBarWM.setAttribute('aria-valuenow', weightWashingMachine);
        const weightPercentageWM = document.getElementById('weight-wm');
        weightPercentageWM.innerHTML = weightWashingMachine + '%';

        weightTumbleDrier = data['Tumble Drier'].shift()
        const progressBarTD = document.getElementById('weight-td');
        progressBarTD.style.width = weightTumbleDrier + '%';
        progressBarTD.setAttribute('aria-valuenow', weightTumbleDrier);
        const weightPercentageTD = document.getElementById('weight-td');
        weightPercentageTD.innerHTML = weightTumbleDrier + '%';

        weightWaterHeater = data['Water Heater'].shift()
        const progressBarWH = document.getElementById('weight-wh');
        progressBarWH.style.width = weightWaterHeater + '%';
        progressBarWH.setAttribute('aria-valuenow', weightWaterHeater);
        const weightPercentageWH = document.getElementById('weight-wh');
        weightPercentageWH.innerHTML = weightWaterHeater + '%';

        weightDishWasher = data['Dish Washer'].shift()
        const progressBarDW = document.getElementById('weight-dw');
        progressBarDW.style.width = weightDishWasher + '%';
        progressBarDW.setAttribute('aria-valuenow', weightDishWasher);
        const weightPercentageDW = document.getElementById('weight-dw');
        weightPercentageDW.innerHTML = weightDishWasher + '%';
    });
}

getConsumerPreferences();

getLoadWeights();
