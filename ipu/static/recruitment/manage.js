var ManageSession = (function() {
	"use strict";

	function clearErrors(el){
		$(el + ' .non-field-errors').remove();
		$(el + ' .errors').remove();
		$(el + ' .input-field').removeClass('has-error');
		$(el + ' .input-field input').removeClass('invalid');
		// for 'error'
		var form_div = $(el).parent().find('.error').remove();
	}
	
	function addErrorsToForm(form_errors, el){
		var form = $(el);
		if(!form || !form_errors)
			return;
		
		if ('__all__' in form_errors){
			var non_field_errors = form_errors['__all__'];
			var div = $('<div class="non-field-errors"/>');
			for (var i=0; i<non_field_errors.length; i++){
				div.append($('<small class="error">' + non_field_errors[i] + '</small>'));
			}
			$(form).prepend(div);
			delete form_errors['__all__'];
		}
		for(var field_name in form_errors){
			$(el + ' #id_'+field_name+'_container').addClass('has-error');
			$(el + ' #id_'+field_name).addClass('invalid');
			var div = $('<div class="errors"/>');
			for(var i=0; i<form_errors[field_name].length; i++){
				div.append($('<small class="error">' + form_errors[field_name][i] + '</small>'));
			}
			$(el + ' #id_'+field_name+'_container').append(div);
		}
	}

	function show_ended_warnings(){
		var checked = this.checked,
			heading = 'Heading',
			message = 'Message',
			type = 'warning',
			application_deadline = new Date($(this).parents('form').find('#id_application_deadline').val()),
			deadline_passed;
		deadline_passed = (new Date()) > application_deadline;
		if (deadline_passed){
			if (checked) {
				heading = 'You have ticked the box';
				message = 'All the students currently in the session, if any, will be notified that they have been selected. To save changes, submit the form.';
			} else {
				heading = 'You have unticked the box';
				message = 'To end the session and to notify the students currently in the session, if any, that they have been selected, tick the box and submit  the form.';
			}
		} else {
			if (checked){
				heading = 'Info';
				message = 'Since application deadline hasn\'t been reached yet, marking the session as ended will have no effect.';
				this.checked = false;
			} else {
				heading = 'Info';
				message = 'To save changes, submit the form.'
			}
		}
		swal(heading, message, type)
	}

	function handleAJAX(form, form_id) {
		clearErrors(form_id);
		var url = $(form).attr('action');
		var type = $(form).attr('method');
		var form_data = new FormData(form[0]);
		$.ajax({
			url: url,
			type: type,
			data: form_data,
			processData: false,
			contentType: false,
			beforeSend: function() {
				showPreloader();
				$(form).find('button').addClass('disabled');
			},
			complete: function() {
				removePreloader();
				$(form).find('button').removeClass('disabled');
			},
			success: function(data, status, xhr){
				/*
				if (data['location']){
					location.href = data['location'];
					return;
				}
				var $span = $('<span class="green-text text-lighten-1" />').html("Success!").css('fontWeight', 'bold');
//				var $span = $('<span class="green-text green-accent-2" />').html("Success!").css('fontWeight', 'bold').css('flexBasis', '80%');
//				var $i = $('<i class="toast-dismiss-icon fa fa-2x fa-times grey-text text-lighten-3"/>');
//				$i.on('click', function(e){$('.toast').remove();});
//				var $p = $('<p class="row"/>').css('display', 'flex').css('justifyContent', 'space-around');
//				Materialize.toast($p.append($span).append($i));
				Materialize.toast($span, 5000);
			
				*/
				if (data.refresh)
					swal({
						title: 'Success!',
						text: data.message,
						type: 'success',
						allowEscapeKey: false,
					}, function(){window.location.href = (data.location ? data.location : '')});
				else
					swal('Success!', data.message, 'success');
			},
			error: function(xhr, status, error){
				/*
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				Materialize.toast($('<span class="flow-text red-text" />').html('Error Occurred.').css('fontWeight', 'bold'), 5000);
				if (xhr.responseJSON['error']){
					$(form).parent().prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
				*/
				if (xhr.responseJSON && xhr.responseJSON['error']){
					$(form).parent().prepend($('<small class="center error">'+xhr.responseJSON['error']+'</small>'))
//					Materialize.toast($('<span class="flow-text red-text" />').html('Error Occurred.').css('fontWeight', 'bold'), 5000);
				}
				var message = (xhr.responseJSON && (xhr.responseJSON['message'] || xhr.responseJSON['error'])) ? (xhr.responseJSON['message'] || xhr.responseJSON['error']) : (xhr.status >= 500 ? 'Sorry, an unexpected error occurred. Please try again after sometime.' : 'Please correct the errors.');
				swal('Error!', message, 'error');
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
			}
		});
	}

	function submitForm(e){
		e.preventDefault();
		handleAJAX($(this), '#' + $(this).attr('id'));
	}

	return {
		init: function(forms){
			for(var i=0; i<forms.length; i++){
				var $form = $('#' + forms[i]);
				$form.on('submit', submitForm);
				$form.find('#id_ended').on('change', show_ended_warnings);
			}
		}
	};
})();
