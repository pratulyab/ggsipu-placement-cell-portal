var DSession = (function() {
	"use strict";
	var	inProcess = {
			'nss': false,
		};
	
	var sessionCounter = 0;

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
		$(el + ' .error').remove();
		$(el + ' .input-field').removeClass('has-error');
		$(el + ' .input-field input').removeClass('invalid');
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

	function addOptionsToSelectField(data, $select_el){
		$select_el.children().slice(1).remove();
		for(var datum of data) {
			var $option = $('<option/>');
			$option.attr('value', datum.value);
			$option.html(datum.html);
			$select_el.append($option);
		}
		$select_el.material_select('destroy');
		$select_el.prop('disabled', false);
		$select_el.material_select();
		Materialize.updateTextFields();
	}

	function notifySessionStudents(e) {
		e.preventDefault();
		var $envelope = $(this),
			$lightbox = $('#light3'),
			$fade = $('#fade3'),
			url = $envelope.attr('href'),
			form = $lightbox.find('#notify-session-students-form');
		$lightbox.css('display', 'flex');
		$fade.css('display', 'flex');
		form.on('submit', function(e){
			e.preventDefault();
			if (inProcess['nss'])
				return;
			form = $(form);
			var form_id = '#'+form.attr('id');
			clearErrors(form_id)
			var form_data = new FormData($(this)[0]);
			inProcess['nss'] = true;
			$.ajax({
				url: url,
				type: 'POST',
				data: form_data,
				processData: false,
				contentType: false,
				success: function(data, status, xhr){
					swal({
							title: "Message has been sent successfully!",
							text: "All the students of the chosen session have been notified",
							type:"success",
							allowEscapeKey: false,
						},
						function() {
							window.location.href = '';
					});
					inProcess['nss'] = false;
				},
				error: function(xhr, status, error){
					if (xhr.responseJSON['error']){
						$(form).parent().prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
					}
					var form_errors = xhr.responseJSON['errors'];
					addErrorsToForm(form_errors, form_id);
					inProcess['nss'] = false;
				}
			});
		});
	}

	function getSessions() {
		sessionCounter++;
		if (sessionCounter >= 10){
			location.href = '';
			return;
		}
		var li = $(this);
		var div = $('#dsess');
		$.ajax({
			url: '/dcompany/mydsessions/',
			type: 'GET',
			data: {},
			success: function(data, status, xhr){
				var loc = data['location'];
				if (loc){
					location.href = loc;
				}
				div.html(data['html']);
				div.find('a.envelope').on('click', notifySessionStudents);
			},
			error: function(status, xhr, error){
				div.html($('<p>' + "Sorry, couldn't retrieve your sessions.<br><br>" + '</p>'));
				if (xhr['error']){
					var p = $('<p/>');
					p.html(xhr['error']);
					div.append(p);
				}
			}
		});
	}

	function getStreams(form, form_id, url) {
		form = $(form_id);
		var programme_el = form.find('#id_programme');
		var programme_value = $(programme_el.children()[programme_el.prop('selectedIndex')]).attr('value');
		$.ajax({
			url: url,
			type: 'GET',
			data: {'programme': programme_value},
			contentData: false,
			success: function(data, status, xhr){
				if (data['location']){
					location.href = data['location'];
					return;
				}
				var streams = data['streams'];
				var years = data['years'];
				var $stream_select = $(form).find('#id_streams');
				var $years_select = $(form).find('#id_years');
				addOptionsToSelectField(streams, $stream_select);
				addOptionsToSelectField(years, $years_select);
//				$(form_id).on('submit', submitForm);
				return;
			},
			error: function(xhr, status, error){
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				if (xhr.responseJSON['error']){
					$(form).prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
//				$(form_id).on('submit', submitForm);
			}
		});
	}

	function getEditDummyCompanyForm(form, form_id, url, value){
		clearErrors(form_id);
		form = $(form_id);
		$.ajax({
			url: url,
			type: 'GET',
			data: {'dcompany_hashid': value},
			contentType: false,
			success: function(data, status, xhr){
				if (data['location']){
					location.href = data['location'];
					return;
				}
				$('#edit-forms-div').append($(data['html']));
				$('#edit-dummy-company-form').on('submit', submitForm);
			},
			error: function(xhr, status, error){
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				if (xhr.responseJSON['error']){
					$(form).prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
//				$(form_id).on('submit', submitForm);
			}
		});
	}

	function handleAJAX(form, form_id, url) {
		clearErrors(form_id);
		form = $(form_id);
		var type = $(form).attr('method');
		var form_data = new FormData(form[0]);
//		form.off('submit');
		$.ajax({
			url: url,
			type: type,
			data: form_data,
			processData: false,
			contentType: false,
			success: function(data, status, xhr){
				if (data['location']){
					location.href = data['location'];
					return;
				}
				if (data.render){
					var form_div = $(form).parent();
					form_div.html(data['render']);
					$(form_id).on('submit', submitForm);
				}
				Materialize.toast('Changes have been saved!', 3000)
//				handleMultipleJquery();
			},
			error: function(xhr, status, error){
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				if (xhr.responseJSON['error']){
					$(form).prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
//				$(form_id).on('submit', submitForm);
			}
		});
	}

	function submitForm(e){
		e.preventDefault();
		clearPrefixFromName('#edit-dummy-company-form', 'dc-');
		handleAJAX($(this), '#' + $(this).attr('id'), $(this).attr('action'));
	}

	return {
		init: function() {
			//
			var form_id = '#create-dummy-session-form';
			var form = $(form_id)
			form.on('submit', submitForm);
			var programme = form.find('#id_programme');
			programme.on('change', function(e){
				getStreams(form, form_id, '/dcompany/dsess_streams/');
			});
			//
			var li = $('#dsessions');
			li.on('click', getSessions);
			//
			var choose_form_id = '#choose-dummy-company-form';
			var choose_form = $(choose_form_id);
			var dummy_company_field = choose_form.find('#id_dummy_company');
			choose_form.on('submit', function(e){
				e.preventDefault();
				var value = $(dummy_company_field.children()[dummy_company_field.prop('selectedIndex')]).attr('value');
				var action = $(this).attr('action');
				getEditDummyCompanyForm(choose_form, choose_form_id, action, value)
			});
			dummy_company_field.on('change', function(e){
				$('#edit-dummy-company-div').remove();
			});
		}
	};
})();
