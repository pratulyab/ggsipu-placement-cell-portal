var Associate = (function() {
	"use strict";

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
		$(el).parent().find('.error').remove();
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

	function get_whatever(form, form_id, url, data) {
		clearErrors(form_id);
		form = $(form_id);
		$.ajax({
			url: url,
			type: 'GET',
			data: data,
			contentType: false,
			success: function(data, status, xhr){
				if (data['programmes']){
					var $programme_select = $(form).find('#id_programme');
					addOptionsToSelectField(data['programmes'], $programme_select);
					var $streams_select = $(form).find('#id_streams');
					$streams_select.children().slice(1).remove()
					$streams_select.material_select();
				}
				if (data['streams']){
					var $streams_select = $(form).find('#id_streams');
					addOptionsToSelectField(data['streams'], $streams_select);
				}
			},
			error: function(xhr, status, error){
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				if (xhr.responseJSON['error']){
					$(form).parent().prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
					Materialize.toast(xhr.responseJSON['error'], 4000);
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
			}
		});
	}

	function handleAJAX(form, form_id, url) {
		clearErrors(form_id);
		form = $(form_id);
		var type = $(form).attr('method');
		var form_data = new FormData(form[0]);
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
				/*
				handleMultipleJquery();
				var form_div = $(form).parent();
				form_div.html(data['render']);
				$(form_id).on('submit', submitForm);
				
				// Reload programmes on college change
				var coll_container = $('#id_college_container');
				if (coll_container.length && !coll_container.find('span.disabled').length)
					coll_container.on('change', function(e){
						handleAJAX(form, form_id, '/recruitment/get_with_prog/');
					});
				
				var prog = $(form_id).find('#id_programme');
				var streams = $(form_id).find('#id_streams');
				if (prog.length && streams.length)
					prog.on('change', function(e){
						handleAJAX(form, form_id, '/recruitment/get_with_streams/');
					});
					*/
			},
			error: function(xhr, status, error){
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				if (xhr.responseJSON['error']){
					$(form).parent().prepend($('<small class="center error">'+xhr.responseJSON['error']+'</small>'))
					Materialize.toast(xhr.responseJSON['error'], 4000);
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
//				$(form_id).on('submit', submitForm);
			}
		});
	}

	function submitForm(e){
		e.preventDefault();
		handleAJAX($(this), '#' + $(this).attr('id'), $(this).attr('action'));
	}

	return {
		init: function(forms) {
			for(var i=0; i<forms.length; i++){
				$('#' + forms[i]).on('submit', submitForm);
			}
			var association_form_id = '#associate-form'
			var association_form = $(association_form_id);
			var college_field = association_form.find('#id_college');
			var programme_field = association_form.find('#id_programme');
			if (college_field)
				college_field.on('change', function(e){
					e.preventDefault();
					var college_value = $(college_field.children()[college_field.prop('selectedIndex')]).attr('value');
					get_whatever(association_form, association_form_id, '/recruitment/get_prog/', {'college': college_value});
				});
			programme_field.on('change', function(e){
				e.preventDefault();
				var programme_value = $(programme_field.children()[programme_field.prop('selectedIndex')]).attr('value');
				var $streams_select = $(association_form).find('#id_streams');
				$streams_select.children().slice(1).remove()
				$streams_select.material_select();
				get_whatever(association_form, association_form_id, '/recruitment/get_streams/', {'programme': programme_value});
			});
		}
	};
})();
