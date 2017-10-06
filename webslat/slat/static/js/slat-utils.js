$(document).ready(function() {

        // JQuery code to be added in here.
 $("#about-btn").click( function(event) {
     //alert($("#form[0].component.value"));
     var k = $("#form[0].component").val();
     k = document.forms[0].component.value;
     //document.forms[0].desc2.value=$.get('/slat/component-description/' + k)
     $.get('/slat/component-description/' + k, function(data) {
	 $("#like_count").html(data);
     });
     //alert(k);
     //alert("You clicked the button using JQuery!");
    });
});
