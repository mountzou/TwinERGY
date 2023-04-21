function getConsumerPreferences() {
    $.getJSON('/get_data_preferences', function (data) {

        // Get the preferences related to the thermal comfort tolerance [min, max values]
        var thermal_comfort_max = data['preferences'][0]['thermal_comfort_preferences']['thermal_comfort_max'];
        var thermal_comfort_min = data['preferences'][0]['thermal_comfort_preferences']['thermal_comfort_min'];

        // Get the preferences related to the thermal comfort tolerance [min, max values]
        var temperature_max = data['preferences'][0]['temperature_preferences']['temperature_max'];
        var temperature_min = data['preferences'][0]['temperature_preferences']['temperature_min'];

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
        })
    });
}

getConsumerPreferences();
