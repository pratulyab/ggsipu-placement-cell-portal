var Notification = (function() {
	'use strict'
	
	function handleMultipleJquery(){
		$('a').unbind('click'); // to prevent multiple fires because of reloading of jquery in the rendered template.
		$('#dropdown3').on('click', function(e){e.stopPropagation();});
		$('.dropdown-button').on('click', function(e){e.preventDefault()});
		$('nav .brand-logo').on('click', function(e){location.href='';});
		$('#dropdown1 a').each(function(i, a){
			var el = $(a);
			var target = el.data('links');
			if (!target)
				return true;
			var target_el = $('#tab-bar').find("[href='#" + target + "']");
			if(!target_el.length)
				return true;
			el.on('click', function(e){e.preventDefault();target_el[0].click();});
		});
	}

	function getForm() {
    	var url = $('#notification').attr('url');
    	$.ajax({
    		url : url,
    		type : 'GET',
    		async : true,
    		success : function(data, status, xhr){
				handleMultipleJquery();
           		$("#notifications").html(data); 
                $('#generate-streams-form').on('submit' , getStreamsSelected);	
    		}
    	});
    }


    function getStudentForm(stream_list, indices) {
        var url = "http://127.0.0.1:8000/notification/select_streams/"
        var token = $('input[name = csrfmiddlewaretoken]').val();
        $.ajax({
            url : url,
            type : 'POST',
            data : { 'csrfmiddlewaretoken' : token,
                     'stream_list' : stream_list,
                     'indices' : indices,
             },
            success : function(data , status , xhr){
				handleMultipleJquery();
                $('#notifications').html(data);
                $('#id_stream').on('change' , getStreamsSelected);
                $('#create_notification-form').on('submit' , getStudentsSelected)
            }
        });
    }

    function submitForm(student_list) {
    	var url = $('#create_notification-form').attr('action')
    	var message = $('#id_message').val();
        var token = $('input[name = csrfmiddlewaretoken]').val();
    	student_list.shift();
    	$.ajax({
    		url : url,
    		type : 'POST',
    		data : { 
                'csrfmiddlewaretoken' : token , 
                'student_list' :student_list,
                'message' : message ,
            },
    		success : function(data , status , xhr){
                $('#notification').trigger('click');
                alert("Successful ! " + data + " students are notified");

    		}
    	});
    }

    function getStudentsSelected(e) {
        e.preventDefault();
        var student_list = [];
        $('#id_students :selected').each(function (i , selected) {
                  student_list[i] = $(selected).text();          
            });
        submitForm(student_list);
    }


    function getStreamsSelected(e) {
        e.preventDefault();
        var stream_list = [];
        var indices = [];
        $("#id_stream :selected").each(function (i , selected) {
                stream_list[i] = $(selected).text().substring(1,4);
                indices[i] = $(selected).index();
            });
        //Blur doesn't work since the dropdown div has a dynamic HTML ID
        getStudentForm(stream_list,indices);        
    }
    function generateForm(e) {
            e.preventDefault();
            getForm();

        }
    

	return {
		init: function() {
			$('#notification').on('click' , generateForm);
		}
	}

})();
