var preloader = document.getElementById('page-preloader');
	var preloader_shadow = document.getElementById('preloader-shadow');

	function showPreloader(){
		var h = window.innerHeight;
 		var w = window.innerWidth;
 		addPreloaderShadow(h , w);
 		preloader.style.top = h/3 + 'px';
 		preloader.style.left = w/2.4 + 'px';
 		preloader.style.display = 'block';
	}

	function addPreloaderShadow(h , w){
		preloader_shadow.style.height = h + 'px';
  		preloader_shadow.style.width = w + 'px';
  		preloader_shadow.style.display = 'block';
	}

	function removePreloader(){
		preloader.style.display = 'none';
		preloader_shadow.style.display = 'none';
	}

var Auth = (function() {
	'use strict';
	var inProcess = {
		'sl': false,
		'ss': false,
		's': false,
		'l': false
	}

	function clearErrors(el){
		$(el + ' .non-field-errors').remove();
		$(el + ' .errors').remove();
		$(el + ' .input-field').removeClass('has-error');
		$(el + ' .input-field input').removeClass('invalid');
		$(el).parent().find('.error').remove();
	}

	function addErrorsToForm(form_errors, el, prefix){
		var form = $(el);
		if(!form || !form_errors)
			return;
		
		if ('__all__' in form_errors){
			var non_field_errors = form_errors['__all__'];
			var div = $('<div class="non-field-errors"/>');
			for (var i=0; i<non_field_errors.length; i++){
				div.append($('<p class="red-text" style="display: block">' + non_field_errors[i] + '</p>'));
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

	function handleAJAX(form, form_id, prefix, submit_event_function) {
		if (inProcess[prefix.slice(0,2)])
			return;
		
		inProcess[prefix.slice(0,2)] = true;
		clearErrors(form_id);
		var url = $(form).attr('action');
		var form_data = new FormData(form[0]);
//		$(form_id).off('submit'); // Not using this method because ajax isn't able to handle multiple requests simultaneously. Hence, when Enter is keep pressed for a long time, one of the request gets missed by JS and gets processed by html (i.e. Synchronous POST)
		// Moreover, we want JS to handle all requests. Therefore, we shouldn't turn off the event listener
		$.ajax({
			url: url,
			type: 'POST',
			data: form_data,
			processData: false,
			contentType: false,
			beforeSend: function() {
   				showPreloader();
            },
            complete: function() {
            	removePreloader();
            },	
			success: function(data, status, xhr){
				if(data['render']){
					$('html').html(data['render']);
					return;
				}
				var loc = data['location'] ? data['location'] : '';
				inProcess[prefix.slice(0,2)] = false;
				location.href = loc;
			},
			error: function(xhr, status, error){
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id, prefix);
				if (xhr.responseJSON && xhr.responseJSON['error']){
					$(form).parent().prepend($('<small class="red-text error">'+xhr.responseJSON['error']+'</small>'))
					if(prefix == 's-' || prefix == 'ss-'){
						grecaptcha.reset();
					}
				}
				inProcess[prefix.slice(0,2)] = false;
//				$(form_id).on('submit', submit_event_function);
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
		handleAJAX($(this), '#login-form', 'l-', login);
	}

	function signup(e) {
		e.preventDefault();
		clearPrefixFromName('#signup-form', 's-');
		handleAJAX($(this), '#signup-form', 's-', signup);
	}

	function studentLogin(e) {
		e.preventDefault();
		clearPrefixFromName('#student-login-form', 'sl-');
		handleAJAX($(this), '#student-login-form', 'sl-', studentLogin);
	}

	function studentSignup(e) {
		e.preventDefault();
		clearPrefixFromName('#student-signup-form', 'ss-');
		handleAJAX($(this), '#student-signup-form', 'ss-', studentSignup);
	}

	function enforcePasswordConstraints(e) {
		var $input = $(this),
			$icon = $input.prev(),
			password = $input.val(),
			title = 'Weak Password',
			error = '',
			texts = [];
		if (! /(?=.*[a-zA-Z]+)/.test(password)) {
			texts.push('- Password must contain at least one alphabet.');
			error = 'Password is entirely numeric.'
		}
		if(! /(?=.*\d)/.test(password)) {
			texts.push('- Password must contain at least one digit.');
			error = 'Include digit(s) in the password.'
		}
		if (! /(?=.*[#!$%&()*+,-./:;<=>?@[\]^_`{|}~])/.test(password)) {
			texts.push('- Password must contain at least one special character.');
			error = 'Include special character(s).'
		}
		if (! /.{8,}/.test(password)) {
			texts.push('- Password must be at least 8 characters long.');
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
		init: function() {
			$('#login-form').on('submit', login);
			$('#signup-form').on('submit', signup);
			$('#student-login-form').on('submit', studentLogin);
			$('#student-signup-form').on('submit', studentSignup);
			$('input[id$=password1]').on('change', enforcePasswordConstraints);
			$('input[id$=password2]').on('change', matchPasswords);
		}
	};
})();
