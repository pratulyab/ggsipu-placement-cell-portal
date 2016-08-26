var Settings = (function() {
	"use strict";

	function clearErrors(el){
		$(el + ' .non-field-errors').remove();
		$(el + ' .errors').remove();
		$(el + ' .input-field').removeClass('has-error');
		$(el + ' .input-field input').removeClass('invalid');
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
			success: function(data, status, xhr){
				var form_div = $(form).parent();
				form_div.html(data);
				$(form_id).on('submit', submitForm);
			},
			error: function(xhr, status, error){
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
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
				$('#' + forms[i]).on('submit', submitForm);
			}
		}
	};
})();
