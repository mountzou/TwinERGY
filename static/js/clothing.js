$(document).ready(function() {

    function getIndexByCustomValue(valuesArray, cloValues, value) {
        for (const key in cloValues) {
            if (cloValues.hasOwnProperty(key) && cloValues[key] === value) {
                return valuesArray.indexOf(key);
            }
        }
        return -1;
    }

    var cloValues = {
      "Tank top & short-shorts": 0.40,
      "T-shirt & short-shorts": 0.43,
      "Tank top & thin-trousers": 0.47,
      "T-shirt & thick-trousers": 0.56,
      "Thin jacket & thin-trousers": 0.71,
      "Thick jacket & thin-trousers": 0.79,
      "Thick jacket & thick-trousers": 0.88,
      "Coveralls": 1.20,
      "Long-sleeve shirt & thin-trousers": 0.60,
      "Long-sleeve sweatshirt & thick-trousers": 0.80
    };

    $("#summer_total_clo").ionRangeSlider({
        grid: !0,
        from: 0,
        to: 3,
        values: ["Tank top & short-shorts", "T-shirt & short-shorts", "Tank top & thin-trousers", "T-shirt & thick-trousers"],
        onChange: function(data) {
            var summer_clo = cloValues[data.from_value];
            document.getElementById('summer-clo').innerHTML = summer_clo + ' clo.'
            $.ajax({
                url: '/update_clothing_summer',
                type: 'POST',
                data: {
                    summer_clo: summer_clo,
                },
                success: function(response) {
                    console.log("Summer outfit updated successfully");
                },
                error: function(response) {
                    console.log("Error updating summer outfit");
                }
            });
        },
    });

    $("#winter_total_clo").ionRangeSlider({
        grid: !0,
        from: 0,
        to: 5,
        values: ["Thin jacket & thin-trousers", "Thick jacket & thin-trousers", "Thick jacket & thick-trousers", "Coveralls"],
        onChange: function(data) {
            var winter_clo = cloValues[data.from_value];
            document.getElementById('winter-clo').innerHTML = winter_clo + ' clo.'
            $.ajax({
                url: '/update_clothing_winter',
                type: 'POST',
                data: {
                    winter_clo: winter_clo,
                },
                success: function(response) {
                    console.log("Winter outfit updated successfully");
                },
                error: function(response) {
                    console.log("Error updating winter outfit");
                }
            });
        },
    });

    $("#autumn_total_clo").ionRangeSlider({
        grid: !0,
        from: 0,
        to: 3,
        values: ["T-shirt & short-shorts", "T-shirt & thick-trousers", "Long-sleeve shirt & thin-trousers", "Long-sleeve sweatshirt & thick-trousers"],
        onChange: function(data) {
            var autumn_clo = cloValues[data.from_value];
            document.getElementById('autumn-clo').innerHTML = autumn_clo + ' clo.'
            $.ajax({
                url: '/update_clothing_autumn',
                type: 'POST',
                data: {
                  autumn_clo: autumn_clo,
                },
                success: function(response) {
                  console.log("Autumn outfit updated successfully");
                },
                error: function(response) {
                  console.log("Error updating autumn outfit");
                }
            });
        },
    });

    $("#spring_total_clo").ionRangeSlider({
        grid: !0,
        from: 0,
        to: 3,
        values: ["T-shirt & short-shorts", "T-shirt & thick-trousers", "Long-sleeve shirt & thin-trousers", "Long-sleeve sweatshirt & thick-trousers"],
        onChange: function(data) {
            var spring_clo = cloValues[data.from_value];
            document.getElementById('spring-clo').innerHTML = spring_clo + ' clo.'
            $.ajax({
                url: '/update_clothing_spring',
                type: 'POST',
                data: {
                  spring_clo: spring_clo,
                },
                success: function(response) {
                  console.log("Spring outfit updated successfully");
                },
                error: function(response) {
                  console.log("Error updating spring outfit");
                }
            });
        },
    });

    $.getJSON('/get_user_clothing_insulation', function (data) {

        document.getElementById('summer-clo').innerHTML = data.summer + ' clo.'
        document.getElementById('winter-clo').innerHTML = data.winter + ' clo.';
        document.getElementById('autumn-clo').innerHTML = data.autumn + ' clo.';
        document.getElementById('spring-clo').innerHTML = data.spring + ' clo.';

        const winter_values = ["Thin jacket & thin-trousers", "Thick jacket & thin-trousers", "Thick jacket & thick-trousers", "Coveralls"];
        const summer_values = ["Tank top & short-shorts", "T-shirt & short-shorts", "Tank top & thin-trousers", "T-shirt & thick-trousers"];
        const spring_values = ["T-shirt & short-shorts", "T-shirt & thick-trousers", "Long-sleeve shirt & thin-trousers", "Long-sleeve sweatshirt & thick-trousers"];
        const autumn_values = ["T-shirt & short-shorts", "T-shirt & thick-trousers", "Long-sleeve shirt & thin-trousers", "Long-sleeve sweatshirt & thick-trousers"];

        const winter_clo_index = getIndexByCustomValue(winter_values, cloValues, data.winter);
        const summer_clo_index = getIndexByCustomValue(summer_values, cloValues, data.summer);
        const spring_clo_index = getIndexByCustomValue(spring_values, cloValues, data.spring);
        const autumn_clo_index = getIndexByCustomValue(autumn_values, cloValues, data.autumn);

        const winter_slider = $("#winter_total_clo").data("ionRangeSlider");
        const autumn_slider = $("#autumn_total_clo").data("ionRangeSlider");
        const summer_slider = $("#summer_total_clo").data("ionRangeSlider");
        const spring_slider = $("#spring_total_clo").data("ionRangeSlider");

        winter_slider.update({ from: winter_clo_index });
        summer_slider.update({ from: summer_clo_index });
        spring_slider.update({ from: spring_clo_index });
        autumn_slider.update({ from: autumn_clo_index });

    });

});