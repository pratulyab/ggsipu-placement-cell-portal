var Notification = (function() {
	'use strict'
    var sphr_create_notification = true;
	var indices = [];
    var preloader = document.getElementById('page-preloader');
    var preloader_shadow = document.getElementById('preloader-shadow');
	function handleMultipleJquery(){
		$('a').unbind('click'); // to prevent multiple fires because of reloading of jquery in the rendered template.
		document.getElementById('create-notifications').removeEventListener('click', generateNewForm);
        $('#dropdown3').on('click', function(e){e.stopPropagation();});
		$('.dropdown-button').on('click', function(e){e.preventDefault()});
		$('nav .brand-logo').on('click', function(e){location.href='';});
        document.getElementById('create-notifications').addEventListener('click', generateNewForm);
         // Handles the left panel notification button.
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

    function generateNewForm(e) {
            e.preventDefault();
            $('#notify-students-div').html(" ");
            getForm();

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
            beforeSend: function() {
                showPreloader();
            },
            complete: function() {
                removePreloader();  
            },
    		success : function(data, status, xhr){
				//handleMultipleJquery();
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
             beforeSend: function() {
                showPreloader();
            },
            complete: function() {
                removePreloader();  
            },
            success : function(data , status , xhr){
				//handleMultipleJquery();
                $('#notify-students-div').html(data);
                $('#id_sms_message_container').hide();
                $("#id_subject").attr('length' , '256');
                $("#id_sms_message").attr('length' , '128');
                $('#id_if_all').on('change' , function(){
                    var el = $('#id_students_container').find('select');
                    if ($(this).is(':checked')) {         
                        el.attr("disabled" , "");
                        el.material_select();
                  } else {
                        el.removeAttr("disabled");
                        el.material_select();
                  }
                });
                $('#id_if_sms').on('change' , function(){
                    if ($(this).is(':checked')) {
                        removeError($('#id_sms_message'));
                        $('#id_sms_message_container').show();
                        $('#id_sms_message').attr('data-length' , '160');
                        $('#id_sms_message').characterCounter();
                  } else {
                        $('#id_sms_message_container').hide();
                  }
                });
                $('#create_notification-form').on('submit' , getStudentsSelected);
                $('#id_stream').on('change' , generateNewForm);
                $('select[id^="id_select_year"]').on('change' , getYearsSelected)
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
        var url = $('#create_notification-form').attr('students');
        var token = $('input[name = csrfmiddlewaretoken]').val();
        $.ajax({
            url : url,
            type : 'POST',
            data : { 
                'csrfmiddlewaretoken' : token , 
                'stream_to_year' : stream_to_year,
                'indices' : indices,
            },
            beforeSend: function() {
                showPreloader();
            },
            complete: function() {
                removePreloader();  
            },
            success : function(data , status , xhr){
                $('#id_stream').on('change' , generateNewForm);
                populateStudents(data)
            }
        });

    }

    function populateStudents(data){
        var student_select = $('#id_students_container').find('#id_students');
        student_select.empty();
        if(data.length === 0){
            student_select.append('<option disabled="">No Students</option>')
        }
        var i = 1;
        for(var username of data){
            var option = '<option value="' + i +'">'+ username +"</option>";
            student_select.append(option);
            i++;
        } 
        student_select.material_select('destroy');
        student_select.prop('disabled', false);
        student_select.material_select();
        Materialize.updateTextFields();
    }

    function getStudentsSelected(e) {
        e.preventDefault();
        var student_list = [];
        $('#id_students :selected').each(function (i , selected) {
                  student_list[i] = $(selected).text();          
            });
        submitNotificationForm(student_list);
    }

//Final function which creates the notification in the database.
    function submitNotificationForm(student_list) {
        if(sphr_create_notification){
            sphr_create_notification = false;
            var url = $('#create_notification-form').attr('action')
            var select_students = $('#id_students')
            var message = $('#id_message').val();
            var subject = $('#id_subject');
            var sms_message = $('#id_sms_message');
            var token = $('input[name = csrfmiddlewaretoken]').val();
            var if_all = $('#id_if_all').prop('checked');
            var if_email = $('#id_if_email').prop('checked');
            var if_sms = $('#id_if_sms').prop('checked');
            fieldEvaluator(subject , 256)
            if(if_sms){
                fieldEvaluator(sms_message , 128);
            }
            if(if_all === true){
                student_list.length = 0;
                $('#id_students option').each(function(){
                    student_list.push($(this).text());
                });
            }
            if(student_list.length === 0){
                addErrors(select_students , "Please select at least 1 Student. If you can't see any students then make sure that you have select the Years of the Stream properly.")
                sphr_create_notification = true;
                return;
            }
            if(student_list.length > 0){
                removeError(select_students);
            }
            if(fieldEvaluator(subject , 256)){
                $.ajax({
                    url : url,
                    type : 'POST',
                    data : { 
                        'csrfmiddlewaretoken' : token , 
                        'student_list' :student_list,
                        'message' : message,
                        'subject' : subject.val(),
                        'if_sms' : if_sms,
                        'sms_message' : sms_message.val(),
                        'if_email' : if_email,
                    },
                    beforeSend: function() {
                        showPreloader();
                    },
                    complete: function() {
                        removePreloader();  
                    },
                    success : function(data , status , xhr){
                        //handleMultipleJquery();
                        $('#your-notifications').trigger('click');
                        swal({
                            title: "Success!",
                            text: data + " Students are Notified.",
                            type: "success",
                            confirmButtonColor: "green",
                            closeOnConfirm: true,
                        });
                    },
                    error: function(data , status , xhr){
                        swal({
                            title: "Error!",
                            text: data.responseJSON.errors,
                            type: "error",
                            confirmButtonColor: "#DD6B55",
                            closeOnConfirm: true,
                        });
                    }
                });
            }
            sphr_create_notification = true;
        }
    }

function fieldEvaluator(input_field , max_length){
    if(!input_field.val()){
            if(!input_field.closest('div').has('small').length){
                addErrors(input_field , "Required Field");
                return 0;
            }
            else
                return 0;
        }
    if(input_field.val()){
        if(input_field.val().length>max_length){
                addErrors(input_field , "Field exceeds it's limit.");
                return 0;
            }
        else{
                removeError(input_field)
                return 1;
            }
        }


}

function addErrors(field , error){
    var field_container = $('#' + field.attr('id') + '_container');
    if(!field_container.has('small').length){
        field_container.append('<small class="help-block error">'+ error +'</small>');
    }
}

function removeError(field){
    var field_container = $('#' + field.attr('id') + '_container');
    field_container.find('small').remove();

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
            beforeSend: function() {
                showPreloader();
            },
            complete: function() {
                $('#notifications_badge').hide();
                removePreloader();  
            },
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
                '<span class="title">' + data[i].actor + '</span>' /*+ '<p><b>'+ data[i].subject +'</b></p>'*/ + '<p>' + data[i].message + '</p>' + '</li>';
        }
        $('#your-notifications-div-ul').html(raw_html);
		Download.serve();

    }    
    function viewNotifications(e) {
        e.preventDefault();
        getNotifications();
    }

//==============================End============================//

	return {
		init: function() {
            document.getElementById('create-notifications').addEventListener('click', generateNewForm);
            document.getElementById('notification').addEventListener('click' , viewNotifications);
			document.getElementById('your-notifications').addEventListener('click' , viewNotifications);
		}
	}

})();
