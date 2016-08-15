var Landing = (function() {
	'use strict';

	function clearErrors(el){
		$(el + ' .non-field-errors').remove();
		$(el + ' .errors').remove();
		$(el + ' .input-field').removeClass('has-error');
		$(el + ' .input-field input').removeClass('invalid');
	}

	function addErrorsToForm(form_errors, el, prefix){
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
			$(el + ' #id_'+prefix+field_name+'_container').addClass('has-error');
			$(el + ' #id_'+prefix+field_name).addClass('invalid');
			var div = $('<div class="errors"/>');
			for(var i=0; i<form_errors[field_name].length; i++){
				div.append($('<small class="error">' + form_errors[field_name][i] + '</small>'));
			}
			$(el + ' #id_'+prefix+field_name+'_container').append(div);
		}
	}

	function handleAJAX(form, form_id, prefix) {
		clearErrors(form_id);
		var url = $(form).attr('action');
		var form_data = new FormData(form[0]);
		$.ajax({
			url: url,
			type: 'POST',
			data: form_data,
			processData: false,
			contentType: false,
			success: function(data, status, xhr){
				if(data['render']){
					$('html').html(data['render']);
					return;
				}
				var loc = data['location'] ? data['location'] : '';
				location.href = loc;
			},
			error: function(xhr, status, error){
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id, prefix);
			}
		});
	}

	function clearPrefixFromName(form_id, prefix) {
		// Removing prefix from name attribute so that request.POST gets populated with the actual fieldnames as keys
		var input_fields = $(form_id + ' input');
		for (var i=0; i<input_fields.length; i++){
			var input = input_fields[i];
			var name = input.getAttribute('name');
			if (typeof name !== typeof undefined && name !== false){
				input.setAttribute('name', name.replace(prefix, ''));
			}
		}
	}
	
	function login(e) {
		e.preventDefault();
		clearPrefixFromName('#login-form', 'l-');
		handleAJAX($(this), '#login-form', 'l-');
	}

	function signup(e) {
		e.preventDefault();
		clearPrefixFromName('#signup-form', 's-');
		handleAJAX($(this), '#signup-form', 's-');
	}

	function studentLogin(e) {
		e.preventDefault();
		clearPrefixFromName('#student-login-form', 'sl-');
		handleAJAX($(this), '#student-login-form', 'sl-');
	}

	function studentSignup(e) {
		e.preventDefault();
		clearPrefixFromName('#student-signup-form', 'ss-');
		handleAJAX($(this), '#student-signup-form', 'ss-');
	}

	return {
		init: function() {
			$('#login-form').on('submit', login);
			$('#signup-form').on('submit', signup);
			$('#student-login-form').on('submit', studentLogin);
			$('#student-signup-form').on('submit', studentSignup);
		}
	};
})();
