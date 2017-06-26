var Settings = (function() {
	"use strict";
	var inProcess = false;

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

	function handleAJAX(form, form_id) {
		// Swal Enabled
		if (inProcess)
			return;
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
				inProcess = true;
				$(form).find('button').addClass('disabled');
				showPreloader();
			},
			complete: function() {
				inProcess = false;
				removePreloader();	
				$(form).find('button').removeClass('disabled');
			},
			success: function(data, status, xhr){
				if (data.refresh) {
					swal({
						title: 'Success',
						text: data.message,
						type: 'success',
						allowEscapeKey: false,
						}, function(e) {
							window.location.href = '';
						}
					);
				} else
					swal("Success!", data.message, "success");

			},
			error: function(xhr, status, error){
				if (xhr.responseJSON && xhr.responseJSON['error']){
					$(form).parent().prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
				if (xhr.responseJSON && xhr.responseJSON['refresh']) {
					swal({
						title: 'Error',
						text: xhr.responseJSON['message'],
						type: 'error',
						allowEscapeKey: false,
						allowOutsideClick: false,
						}, function(e) {
							window.location.href = xhr.responseJSON['location'] ? xhr.responseJSON['location'] : '';
						}
					);
				} else
					swal("Error!", xhr.responseJSON['message'] , "error");
			}
		});
	}

	function submitForm(e){
		e.preventDefault();
		handleAJAX($(this), '#' + $(this).attr('id'));
	}

	function enforcePasswordConstraints(e) {
		var $input = $(this),
			$icon = $input.prev(),
			password = $input.val(),
			title = 'Weak Password',
			error = '',
			texts = [];
		if (! /(?=.*[a-zA-Z]+)/.test(password)) {
			texts.push('Password must contain at least one alphabet.');
			error = 'Password is entirely numeric.'
		}
		if(! /(?=.*\d)/.test(password)) {
			texts.push('Password must contain at least one digit.');
			error = 'Include digit(s) in the password.'
		}
		if (! /(?=.*[#!$%&()*+,-./:;<=>?@[\]^_`{|}~])/.test(password)) {
			texts.push('Password must contain at least one special character.');
			error = 'Include special character(s).'
		}
		if (! /.{8,}/.test(password)) {
			texts.push('Password must be at least 8 characters long.');
			error = 'Password is too short.'
		}
		if (! error) {
			// No constraint violations
			$icon.removeClass('red-text').addClass('green-text');
			$icon.html('done');
		} else {
			$icon.removeClass('green-text').addClass('red-text');
			$icon.html('report_problem');
			swal({
				title: title,
				text: texts.join('\n'),
				type: 'warning',
				allowOutsideClick: true,
				confirmButtonText: 'Ok, let me correct it.'
			});
			swal.showInputError(error);
		}
	}

	function matchPasswords(e) {
		var $input = $(this),
			$icon = $input.prev();
		if ($input.val() != $input.parents('div.row').prev().find('input').val()) {
			swal({
				title: 'Uh Oh!',
				text: 'Passwords don\'t match. Please re-enter the password.',
				type: 'warning',
				allowOutsideClick: true,
				confirmButtonText: 'OK, let me correct it.'
			});
			$icon.removeClass('green-text').addClass('red-text');
			$icon.html('report_problem');
			swal.showInputError("Passwords don't match!");
		} else {
			$icon.removeClass('red-text').addClass('green-text');
			$icon.html('done');
		}
	}

	return {
		init: function(forms){
			for(var i=0; i<forms.length; i++){
				$('#' + forms[i]).on('submit', submitForm);
			}
			$('input[id$=password1]').on('change', enforcePasswordConstraints);
			$('input[id$=password2]').on('change', matchPasswords);
		}
	};
})();
