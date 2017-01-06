var Notification = (function() {
	'use strict';
	
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
           		$("#notify-students-div").html(data); 
                $('#generate-streams-form').on('submit' , getStreamsSelected);	
    		}
    	});
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

    function getStudentForm(stream_list, indices) {
//        var url = "http://127.0.0.1:8000/notification/select_streams/"
        var token = $('input[name = csrfmiddlewaretoken]').val();
        $.ajax({
            url : '/notification/select_streams/',
            type : 'POST',
            data : { 'csrfmiddlewaretoken' : token,
                     'stream_list' : stream_list,
                     'indices' : indices,
             },
            success : function(data , status , xhr){
				handleMultipleJquery();
                $('#notify-students-div').html(data);
                $('#id_stream').on('change' , getStreamsSelected);
                $('#create_notification-form').on('submit' , getStudentsSelected)
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
                $('#your-notifications').trigger('click');
                alert("Successful ! " + data + " students are notified");

    		}
    	});
    }


    function populateDiv(data) {
        var raw_html = '';  
        var icon = '';                   
        for(var i = (data.length-1) ; i > -1 ; i--){
            console.log("Bleh");
            icon = ( (data[i].read === true) ? '<i class="material-icons circle blue">done_all</i>' : '<i class="material-icons circle red">trending_flat</i>');
            raw_html += '<li class="collection-item avatar">' + icon + 
                '<span class="title">' + data[i].actor + '</span>' + '<p>' + data[i].message + '</p>' + '</li>';
        }
        $('#your-notifications-div-ul').html(raw_html);


    }


    function getNotifications() {
        var url = $('#notification_button').attr('href');
        $.ajax({
            url : url,
            type : 'GET',
            async : true,
            success : function(data, status, xhr){
                populateDiv(data);
            }
        });
        
    }
    function generateForm(e) {
            e.preventDefault();
            getForm();

        }
    
    
    function viewNotifications(e) {
        e.preventDefault();
        getNotifications();
    }


	return {
		init: function() {
            $('#create-notifications').on('click' , getForm)
            $('#notification').on('click' , viewNotifications)
			$('#your-notifications').on('click' , viewNotifications);
		}
	}

})();
