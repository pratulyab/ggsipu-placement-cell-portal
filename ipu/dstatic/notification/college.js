var Notification = (function() {
	'use strict'
	var indices = [];
	function handleMultipleJquery(){
		$('a').unbind('click'); // to prevent multiple fires because of reloading of jquery in the rendered template.
		$('#dropdown3').on('click', function(e){e.stopPropagation();});
		$('.dropdown-button').on('click', function(e){e.preventDefault()});
		$('nav .brand-logo').on('click', function(e){location.href='';});
        $('#create-notifications').on('click' , generateNewForm); // Handles the left panel notification button.
        $('#notification-anchor').on('click' , function(e){$('#your-notifications').trigger('click');});//Handles the maine notification tab button.
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
//Notification Starts.
//Follow the flow. Up to Down.
//Gets the first form. Asks to select the streams.
	function getForm() {
    	var url = $('#notification').attr('url');
    	$.ajax({
    		url : url,
    		type : 'GET',
    		async : true,
    		success : function(data, status, xhr){
				handleMultipleJquery();
           		$("#notify-students-div").html(data); 
                $('#select_streams-form').on('submit' , getStreamsSelected);	
                

    		}
    	});
    }


    function getStreamsSelected(e) {
        e.preventDefault();
        var stream_list = [];
        $("#id_stream :selected").each(function (i , selected) {
                stream_list[i] = $(selected).text().substring(1,4);
                indices[i] = $(selected).index();
            });
        //Blur doesn't work since the dropdown div has a dynamic HTML ID
        getYearForm(stream_list,indices);        
    }

//Asks the user to select the year of respective chosen streams.
    function getYearForm(stream_list, indices) {
        var url = $('#select_streams-form').attr('action');
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
                $('#notify-students-div').html(data);
                $('#id_stream').on('change' , generateNewForm);
                $('#select_year-form').on('submit' , getYearsSelected);
            }
        });
    }
    function getYearsSelected(e) {
        e.preventDefault();
        var stream_to_year = {};
        
        
        var year_list = $("select[name^='select_year_']").each(function() {
            var id = $(this).attr('id');
            var year_selected_list = [];
            $('#' + id + ' :selected').each(function (i, selected) {
                if($(selected).attr('value') !== "" )
                    year_selected_list.push($(selected).text().substring(5));
                
                id = id.substring(id.length - 3);
                
            });       
            stream_to_year[id] = year_selected_list;

        });
        submitYearForm(JSON.stringify(stream_to_year));
        
    }
        
    function submitYearForm(stream_to_year) {
        var url = $('#select_year-form').attr('action');
        var token = $('input[name = csrfmiddlewaretoken]').val();
        $.ajax({
            url : url,
            type : 'POST',
            data : { 
                'csrfmiddlewaretoken' : token , 
                'stream_to_year' : stream_to_year,
                'indices' : indices,
            },
            success : function(data , status , xhr){
                handleMultipleJquery();
                $('#notify-students-div').html(data);
                $('#id_stream').on('change' , generateNewForm);
                $('#id_if_all').on('change' , function(){
                    var el = $('#id_students_container').find('select');
                    if ($(this).is(':checked')) {         
                        el.attr("disabled" , "");
                        el.material_select();
                  } else {
                        el.removeAttr("disabled");
                        el.material_select();
                  }
                })
                $('#create_notification-form').on('submit' , getStudentsSelected);
                
                //$('#id_if_all').on('click' , function(){
                    //if($(this).prop("checked")){
                        //$('#id_students option').attr('selected' , 'selected');
                    //}
                    //else{
                        //console.log("unchecked"); }       

            }
        });

    }
    function getStudentsSelected(e) {
        e.preventDefault();
        var student_list = [];
        $('#id_students :selected').each(function (i , selected) {
                  student_list[i] = $(selected).text();          
            });
        submitNotificationForm(student_list);
    }

//Final function which creates the notification ion the database.
    function submitNotificationForm(student_list) {
        var url = $('#create_notification-form').attr('action')
        var message = $('#id_message').val();
        var token = $('input[name = csrfmiddlewaretoken]').val();
        var if_all = $('#id_if_all').prop('checked');
        if(if_all === true){
            student_list.length = 0;
            $('#id_students option').each(function(){
                student_list.push($(this).text());
            });
        }
        student_list.shift();
        var if_email = $('#id_if_email').prop('checked');
        var if_sms = $('#id_if_sms').prop('checked');
        $.ajax({
            url : url,
            type : 'POST',
            data : { 
                'csrfmiddlewaretoken' : token , 
                'student_list' :student_list,
                'message' : message,
                'if_sms' : if_sms,
                'if_email' : if_email,
            },
            success : function(data , status , xhr){
                //handleMultipleJquery();
                $('#your-notifications').trigger('click');
                alert("Successful ! " + data + " students are notified");

            }
        });
    }
//Create Notification Ends.


//==============================================================================//
//============Below are functions to get a college's notifications.=============//
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

    function populateDiv(data) {
        var raw_html = '';  
        var icon = '';
        if(data.length === 0){
            icon = '<i class="material-icons circle">report_problem</i>' 
            raw_html = '<li class="collection-item avatar">' + icon + '<span class="title">' + 'None' + '</span>' + '<p>' + 'No notifications found.' + '</p>' + '</li>';
            $('#your-notifications-div-ul').html(raw_html);
            return;
        }                   
        for(var i = 0 ; i < data.length ; i++){
            icon = ( (data[i].read === true) ? '<i class="material-icons circle blue">done_all</i>' : '<i class="material-icons circle red">fiber_new</i>');
            raw_html += '<li class="collection-item avatar">' + icon + 
                '<span class="title">' + data[i].actor + '</span>' + '<p>' + data[i].message + '</p>' + '</li>';
        }
        $('#your-notifications-div-ul').html(raw_html);


    }



    function generateNewForm(e) {
            e.preventDefault();
            $('#notify-students-div').html(" ");
            getForm();

        }
    
    
    function viewNotifications(e) {
        e.preventDefault();
        getNotifications();
    }

//==============================End============================//

	return {
		init: function() {
            $('#create-notifications').on('click' , generateNewForm);
            $('#notification').on('click' , viewNotifications);
			$('#your-notifications').on('click' , viewNotifications);
		}
	}

})();
