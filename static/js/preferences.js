function getConsumerPreferences() {
    $.getJSON('/get_data_preferences', function (data) {

        // Get the preferences related to the thermal comfort tolerance [min, max values]
        var thermal_comfort_max = data['preferences'][0]['thermal_comfort_preferences']['thermal_comfort_max'];
        var thermal_comfort_min = data['preferences'][0]['thermal_comfort_preferences']['thermal_comfort_min'];

        $("#preference_thermal_comfort").ionRangeSlider({
          grid: !0,
          type: 'double',
          from: thermal_comfort_min+3,
          to: thermal_comfort_max+3,
          values: ["Cold", "Cool", "Slightly Cool", "Neutral", "Slightly Warm", "Warm", "Hot"],
          onChange: function(data) {
            var fromValue = data.from - 3;
            var toValue = data.to - 3;
            console.log("New values: " + fromValue + ", " + toValue);
              $.ajax({
                url: '/update_preferences',
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
        })
    });
}

getConsumerPreferences();
