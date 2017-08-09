// Help form recaptcha callback.
var Notification = (function() {
	'use strict'
	function handleMultipleJquery(){
		$('a').unbind('click');
		document.getElementById('help').removeEventListener('click', generateNewHelpForm); // to prevent multiple fires because of reloading of jquery in the rendered template.
		!is_mobile_view ? document.getElementById('view-issues').removeEventListener('click', generateIssueList) : document.getElementById('m-view-issues').removeEventListener('click', generateIssueList);
		$('#dropdown3').on('click', function(e){e.stopPropagation();});
		$('.dropdown-button').on('click', function(e){e.preventDefault()});
		$('nav .brand-logo').on('click', function(e){location.href='';});
		document.getElementById('help').addEventListener('click', generateNewHelpForm);//Re-Binds help button in vertical tab.
        !is_mobile_view ? document.getElementById('view-issues').addEventListener('click' , generateIssueList) : document.getElementById('m-view-issues').addEventListener('click' , generateIssueList);
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
    		beforeSend: function() {
   				showPreloader();
            },
            complete: function() {
            	$('select').material_select();
            	var site_key = document.getElementById('submit-issue-recaptcha-div').getAttribute('site-key');
            	grecaptcha.render('submit-issue-recaptcha-div', {
            			'sitekey': site_key,
            	});
            	var delayRemover = 2000; 
				setTimeout(function() {
					removePreloader();
				}, delayRemover);
            },
    		success : function(data, status, xhr){
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
						 'recaptcha_response' : grecaptcha.getResponse(),
				},
				beforeSend: function() {
   					showPreloader();
	            },
	            complete: function() {
	            	removePreloader();	
	            },
				success : function(data , status , xhr){
					!is_mobile_view ? document.getElementById('view-issues').click() : document.getElementById('m-view-issues').click();
					swal({
						title: "Success!",
						text: "Successful! A faculty will get back to you soon.",
						type: "success",
						confirmButtonColor: "green",
						closeOnConfirm: true,
					});
				},
				error: function(data , status , xhr){
					swal({
					title: "Error!",
					text: data.responseJSON.errors,
					type: "warning",
					confirmButtonColor: "#DD6B55",
					closeOnConfirm: true,
				});
				},
			});
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
		var url = !is_mobile_view ? $('#view-issues').attr('url') : $('#m-view-issues').attr('url');
		$.ajax({
			url : url,
			type : 'GET',
			beforeSend: function() {
   				showPreloader();
            },
            complete: function() {
            	removePreloader();	
            },
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
				reply_anchor = '<div class="col s3 itemBox center-align"><a href="" identifier='+ data[i].identifier +'><i class="material-icons ">reply</i><div class="caption">View Reply</div></a></div>';
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
			raw_html+= '<li class="collection-item avatar">' + icon +
				'<div class="row" style="margin-bottom : 0%"><div class="col s9"><span class="title">' + "Issue Type :   " + issue_type + "</span>" +
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
			beforeSend: function() {
   				showPreloader();
            },
            complete: function() {
            	removePreloader();	
            },
			success : function(data , status , xhr){
				$('#view-issues-div').html(data);
				document.getElementById('ok-view-solution').addEventListener('click' , function(e){document.getElementById('your-notifications').click();});
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
			beforeSend: function() {
   				showPreloader();
            },
            complete: function() {
            	$('#notifications_badge').hide();
            	removePreloader();	
            },
            success : function(data, status, xhr){
                populateNotificationDiv(data);    
            }
        });
        
    }

    function populateNotificationDiv(data) {
        var raw_html = '';  
        var icon = '';
        var reply_anchor = '';
        var subject = ''; // Handles subject for notification and message for ping.
        var anchor_space = 'col s12';
        if(data.length === 0){
            icon = '<i class="material-icons circle">report_problem</i>' 
            raw_html = '<li class="collection-item avatar">' + icon + '<span class="title">' + 'None' + '</span>' + '<p>' + 'No notifications found.' + '</p>' + '</li>';
            $('#your-notifications-div-ul').html(raw_html);
            return;
        }                   
    	for(var i = 0 ; i < data.length ; i++){
    		if(!data[i].if_ping){
    			reply_anchor = '<div class="col s3 itemBox center-align"><a href="" identifier='+ data[i].identifier +'><i class="material-icons ">reply</i><div class="caption">View Details</div></a></div>';
    			subject = data[i].subject;
    			anchor_space = 'col s9';
    		}
    		else{
    			reply_anchor = '';
    			subject = data[i].message
    		}
            icon = ( (data[i].read === true) ? '<i class="material-icons circle blue">done_all</i>' : '<i class="material-icons circle red">fiber_new</i>');
            raw_html += '<li class="collection-item avatar">' + icon +
				'<div class="row" style="margin-bottom : 0%"><div class="' + anchor_space + '"><span class="title">' + data[i].actor + "</span>" +
				'<p>' + subject + '</p></div>' + reply_anchor +'</div></li>';
        $('#your-notifications-div-ul').html(raw_html);
        $('#your-notifications-div-ul').find('a').on('click' , function(e) {
			e.preventDefault();
			var param = '';
			param = $(this).attr('identifier');

			viewNotificationDetails(param);
			});
    	}
    }
    function viewNotificationDetails(identifier){
    	var url = $('#your-notifications-div').attr('detail-url');
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
				$('#notification-modal-heading').html(data.subject);
				$('#notification-modal-text').html(data.message);
				$('#notification-modal-date').html(data.date);		
				document.getElementById('notification-detail-modal-trigger').click();
			}
    	});
    }

	function viewNotifications(e) {
        e.preventDefault();
        getNotifications();
    }

//==============================End============================//


	return {
		init: function() {
			document.getElementById('notification').addEventListener('click' , viewNotifications);
			document.getElementById('your-notifications').addEventListener('click' , viewNotifications);
			document.getElementById('help').addEventListener('click' , generateNewHelpForm)
			document.getElementById('view-issues').addEventListener('click' , generateIssueList);
			document.getElementById('report-form-anchor').addEventListener('click' , initializeReportBugModal);
			// mobile
			document.getElementById('m-your-notifications').addEventListener('click' , viewNotifications);
			document.getElementById('m-help').addEventListener('click' , generateNewHelpForm)
			document.getElementById('m-view-issues').addEventListener('click' , generateIssueList);
			document.getElementById('m-report-form-anchor').addEventListener('click' , initializeReportBugModal);
		},
	}

})();
