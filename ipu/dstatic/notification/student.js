var Notification = (function() {
	'use strict'
	function handleMultipleJquery(){
		$('a').unbind('click');
		$('#submit_issue-form').unbind(); // to prevent multiple fires because of reloading of jquery in the rendered template.
		$('#dropdown3').on('click', function(e){e.stopPropagation();});
		$('.dropdown-button').on('click', function(e){e.preventDefault()});
		$('nav .brand-logo').on('click', function(e){location.href='';});
		$('#help').on('click' , generateNewHelpForm);//Re-Binds help button in vertical tab.
        $('#view-issues').on('click' , generateIssueList);
        $('#notification').on('click' , function(e){$('#your-notifications').trigger('click');});//Handles the maine notification tab button.
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

//=============================================================================//
//========Below are functions to handle Help functonality of a Student.========//
	function generateNewHelpForm(e) {
            e.preventDefault();
            $('#help-div').html(" ");
            getHelpForm();

        }

	function getHelpForm(){
		var url = $('#notification').attr('url');
		$.ajax({
    		url : url,
    		type : 'GET',
    		success : function(data, status, xhr){
           		handleMultipleJquery();
           		$("#help-div").html(data);
           		$("#id_subject").attr('length' , '32');
           		$('#submit_issue-form').on('submit' , submitIssueForm); 
           			
    		}
    	});
		
	}

	function submitIssueForm(e){
		e.preventDefault();
		var token = $('input[name = csrfmiddlewaretoken]').val();
		var url = $('#submit_issue-form').attr('action');
		var issue_type = $('#id_issue_type :selected').val();
		var subject = $('#id_subject');
		var message = $('#id_message');
		fieldEvaluator(subject , 32);
		fieldEvaluator(message , 2044);
		if((fieldEvaluator(subject , 32) &&
		fieldEvaluator(message , 2044))){
			$.ajax({
				url : url,
				type : 'POST',
				data : { 'csrfmiddlewaretoken' : token,
						 'issue_type' : issue_type,
						 'subject' : subject.val(),
						 'message' : message.val(),

				},
				success : function(data , status , xhr){
					$('#view-issues').trigger('click');
					alert("Successful! Please check again after sometime for the reply.");
				},
				error: function(error){
					alert("Couldn't Submit! Please try again later.");
				},
			});
			 $("#submit_issue-form").unbind('submit');
		}	
	}

function fieldEvaluator(input_field , max_length){
	if( !input_field.val()){
			if(!input_field.closest('div').has('small').length){
				input_field.closest('div').append('<small class="help-block error">Required field.</small>');
				return 0;
			}
			else
				return 0;
		}
	if(input_field.val()){
		if(input_field.val().length>max_length){
			input_field.closest('div').append('<small class="help-block error">Message is too long.</small>');
			return 0;
			}
		else
			return 1;
		}


}
//=====================================End.=======================================//




//=====================View Solution to Issues functionality======================//

	function generateIssueList(e){
		e.preventDefault();
		$('#view-issues-div').html('<ul id = "view-issues-div-ul" class="collection"></ul>');
		var url = $('#view-issues').attr('url');
		$.ajax({
			url : url,
			type : 'GET',
			success : function(data , status , xhr){
				populateIssueListDiv(data);

			}
		});

	}


	function populateIssueListDiv(data){
		var raw_html = '';
		var icon = '';
		var reply_anchor = '';
		var issue_type = '';		
		if(data.length === 0){
			icon = '<i class="material-icons circle">report_problem</i>' 
            raw_html = '<li class="collection-item avatar">' + icon + '<span class="title">' + 'None' + '</span>' + '<p>' + 'No issues reported by you so far.' + '</p>' + '</li>';
            $('#view-issues-div-ul').html(raw_html);
            return;
		}
		for(var i=0; i<(data.length);i++){
			if(data[i].is_solved === true) {
				icon = '<i class="material-icons circle blue">done_all</i>' ;
				reply_anchor = '<div class="col s2 itemBox"><a href="" identifier='+ data[i].identifier +'><i class="material-icons ">reply</i><div class="caption">View Reply</div></a></div>';
			}
			else {
				icon = '<i class="material-icons circle grey">indeterminate_check_box</i>';
				reply_anchor = '';
			}
			if(data[i].issue_type === 'V')
				issue_type = 'Verification';
			else if(data[i].issue_type === 'P')
				issue_type = 'Placement';
			else if(data[i].issue_type === 'G')
				issue_type = 'General';
			raw_html+= '<li identifier class="collection-item avatar">' + icon +
				'<div class="row"><div class="col s10"><span class="title">' + "Issue Type :   " + issue_type + "</span>" +
				'<p>' + "Subject :   " + data[i].subject + '</p></div>' + reply_anchor +'</div></li>'
		}
		
		$('#view-issues-div-ul').html(raw_html);
		
		$('#view-issues-div-ul').find('a').on('click' , function(e) {
			e.preventDefault();
			var param = '';
			param = $(this).attr('identifier');

			viewIssueReply(param);
		});

	}
	function viewIssueReply(identifier){
		var url = $('#view-issues-div').attr('url')
		$.ajax({
			url : url,
			type : 'GET',
			data : {
				'identifier' : identifier,
			},
			success : function(data , status , xhr){
				handleMultipleJquery();
				$('#view-issues-div').html(data);
				$('#ok').on('click' , function(e){$('#your-notifications').trigger('click');});
			}
		})
	}

//=====================================End.=======================================//




//==============================================================================//
//============Below are functions to get a student's notifications.=============//
	function getNotifications() {
        var url = $('#notification_button').attr('href');
        $.ajax({
            url : url,
            type : 'GET',
            async : true,
            success : function(data, status, xhr){
                populateNotificationDiv(data);
                
            }
        });
        
    }

    function populateNotificationDiv(data) {
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

	function viewNotifications(e) {
        e.preventDefault();
        getNotifications();
    }

//==============================End============================//


	return {
		init: function() {
			$('#notification').on('click' , viewNotifications);
			$('#your-notifications').on('click' , viewNotifications);
			$('#help').on('click' , generateNewHelpForm);
			$('#view-issues').on('click' , generateIssueList);


		}
	}

})();
