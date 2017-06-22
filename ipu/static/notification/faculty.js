var Notification = (function() {
	'use strict'
    var sphr_create_notification = true;
    var indices = [];
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
                addErrors(select_students , "Please select at least 1 Student.")
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
                        $('#your-notifications').trigger('click');
                        alert("Successful ! " + data + " students are notified");

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
//======================Create Notification Ends.===========================//


	function getIssuesList(e) {
		e.preventDefault();
		$('#view-issues-div').html('<ul id = "view-issues-div-ul" class="collection"></ul>');
		var url = $('#view-issues').attr('url')
		$.ajax({
			url:url,
			type : 'GET',
            beforeSend: function() {
                showPreloader();
            },
            complete: function() {
                removePreloader();  
            },
			success: function(data , status , xhr){
				populateHelpDiv(data);
			}
		});
	}

	function populateHelpDiv(data){
		var raw_html = '';
		var icon = '';
		var reply_anchor = '';
        var marked_anchor = '';
		var issue_type = '';		
		if(data.length === 0){
			icon = '<i class="material-icons circle">report_problem</i>' 
            raw_html = '<li class="collection-item avatar">' + icon + '<span class="title">' + 'None' + '</span>' + '<p>' + 'No issues reported so far.' + '</p>' + '</li>';
            $('#view-issues-div-ul').html(raw_html);
            return;
		}
		for(var i=0; i<(data.length);i++){
			if(data[i].is_solved === true) {
				icon = '<i class="material-icons circle blue">done_all</i>' ;
				reply_anchor = '';
                marked_anchor = '';
			}
			else {
				icon = '<i class="material-icons circle red">fiber_new</i>';
                reply_anchor = '<div class="col s1 itemBox"><a href="" identifier='+ data[i].identifier +'><i class="material-icons ">reply</i><div class="caption">Reply</div></a></div>';
                if(data[i].is_marked === true){
                    marked_anchor = '<div class="col s3 itemBox"><a name="mark" href="" identifier='+ data[i].identifier +'><i class="material-icons ">label</i><div class="caption">Marked Important</div></a></div>';
                }
                else{
                    marked_anchor = '<div class="col s3 itemBox"><a name="mark" href="" identifier='+ data[i].identifier +'><i class="material-icons ">label_outline</i><div class="caption">Mark Important</div></a></div>';
                }
			}
			if(data[i].issue_type === 'V')
				issue_type = 'Verification';
			else if(data[i].issue_type === 'P')
				issue_type = 'Placement';
			else if(data[i].issue_type === 'G')
				issue_type = 'General';
			raw_html+= '<li identifier class="collection-item avatar">' + icon +
				'<div class="row"><div class="col s8"><span class="title">' + "BY :   " + data[i].actor + "</span>" +
				'<p>' + "Type :   " + issue_type + '</p></div>' + marked_anchor + reply_anchor +'</div></li>'
		}
		$('#view-issues-div-ul').html(raw_html);
		$('#view-issues-div-ul').find('a').on('click' , function(e) {
			e.preventDefault();
			var param = '';
			param = $(this).attr('identifier');
            if($(this).attr('name') === 'mark'){
                markIssueImportant(param);
                return;
            }

			viewSolveIssueForm(param);
		});
		
	}
    function markIssueImportant(identifier){
        var url = $('#view-issues').attr('markurl');
        $.ajax({
            url : url,
            type : 'GET',
            data : {
                'identifier' : identifier,
            },
            beforeSend: function() {
                showPreloader();
            },
            complete: function() {
                removePreloader();  
            },
            success : function(data , status , xhr){
                document.getElementById('view-issues').click();
            }
        });

    }

	function viewSolveIssueForm(identifier){
		var url = $('#view-issues-div').attr('url')
		$.ajax({
			url : url,
			type : 'GET',
			data : {
				'identifier' : identifier,
			},
            beforeSend: function() {
                showPreloader();
            },
            complete: function() {
                removePreloader();  
            },
			success : function(data , status , xhr){
				handleMultipleJquery();
				$('#view-issues-div').html(data);
                $('#solve').on('click' , submitSolution);
			}
		});
	}
    function submitSolution(e){
        e.preventDefault();
        var url = $('#view-issues-div').attr('url');
        var identifier = $('#submit-solution-form').attr('identifier');
        var token = $('input[name = csrfmiddlewaretoken]').val();
        var email = false;
        if($('#id_if_email').prop("checked")){
            email = true
        }
        var message_field = $('#id_reply');
        var message = $('#id_reply').val();
        fieldEvaluator(message_field , 4095);
        if(fieldEvaluator(message_field , 4095)){
            $.ajax({
                url : url,
                type : 'POST',
                data : { 
                    'csrfmiddlewaretoken' : token , 
                    'identifier' : identifier,
                    'reply' : message,
                    'if_email' : email,
                },
                beforeSend: function() {
                    showPreloader();
                },
                complete: function() {
                    removePreloader();  
                },
                success : function(data , status , xhr){
                    document.getElementById('view-issues').click();
                    alert("Successful! Your solution is submitted.");

                }
            });
        }
    }

//==============================================================================//
//============Below are functions to get a faculty's notifications.=============//
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
            document.getElementById('create-notifications').addEventListener('click', generateNewForm);
            document.getElementById('notification').addEventListener('click' , viewNotifications);
			document.getElementById('your-notifications').addEventListener('click' , viewNotifications);
			document.getElementById('view-issues').addEventListener('click' , getIssuesList);
		}
	}

})();


