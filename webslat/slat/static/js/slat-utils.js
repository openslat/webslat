$(document).ready(function() {

    $("#id_component").change( function(event) {
	k = document.forms[0].component.value;
	if (k) {
	    $.get('/slat/component-description/' + k, function(data) {
		$("#like_count").html(data);
	    })};
    });
    $("#id_component").change();
    
});
