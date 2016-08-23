var Notification = (function() {
	'use strict'

	function getForm() {
    	var options;
    	var url = $('#notification').attr('url');
    	$.ajax({
    		url : url,
    		type : 'GET',
    		async : true,
    		success : function(data, status, xhr){
           		$("#tab3").html(data);
           		$("#generate-notification-form").on('submit', submitNotification);  			
    		}
    	});
    }
    function submitForm(form) {
    	var url = $(form).attr('action')
    	console.log(url);
    	var message = $('#id_message').val();
    	console.log(message);
    	var form = $(this);
    	var post_data = new FormData(form[0]);
    	$.ajax({
    		url : url,
    		type : 'POST',
    		data : { message : message },
    		success : function(data , status , xhr){
    			console.log("ok2");
    		}
    	});
    }
        
	function generateForm(e) {
		e.preventDefault();
		getForm();

	}

	function submitNotification(e) {
		console.log("ok1");
		e.preventDefault();
		submitForm($(this));
	}


	return {
		init: function() {
			$('#notification').click(generateForm);

		}
	}


})();