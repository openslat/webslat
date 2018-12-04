$(document).ready(function() {
    $("#id_component").change();
});

var change_component = function() {
          console.log("CHANGED");
          k = document.forms[0].component.value;
          console.log(k)
          if (k) {
              $.get('/slat/component-description/' + k, function(data) {
                  $("#component_description").html(data);
              })}};

