var Dissociation = (function() {
	var inProcess = {
		'create-dissociation': false,
	}

	function deleteDissociation(e){
		e.preventDefault();
		var url = $(this).attr('href'),
			name = $(this).parent().parent().find('span.title').text();
		swal({
			title: "Unblock " + name + "?",
			text: "Unblocking the user will allow both of you to send association requests once again.",
			type: "warning",
			showCancelButton: true,
			confirmButtonColor: "#DD6B55",
			confirmButtonText: "Yes, delete it!",
			closeOnConfirm: false,
			showLoaderOnConfirm: true,
			allowEscapeKey: false,
			allowOutsideClick: true,
			},
			function(){
				$.ajax({
					url: url,
					type: 'POST',
					data: {'csrfmiddlewaretoken': $('input[name = csrfmiddlewaretoken]').first().val()},
					success: function(data, status, xhr){
						swal({
							title: "Unblocked!",
							text: "The user has been unblocked. If you wish to block users, head over to the other tab.",
							type: "success",
							allowEscapeKey: false,
							},function(){window.location.href = '';}
						);
					},
					error: function(xhr, status, error){
						var error_msg = xhr.responseJSON['error'] ? xhr.responseJSON['error'] : "Sorry, unexpected error occurred.";
						swal("Error!", error_msg, "error");
					},
				});
			});
	}

	function clearErrors(el){
		$(el + ' .non-field-errors').remove();
		$(el + ' .errors').remove();
		$(el + ' .input-field').removeClass('has-error');
		$(el + ' .input-field input').removeClass('invalid');
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

	function createDissociation(e){
		e.preventDefault();
		if (inProcess['create-dissociation'])
			return;
		var	form = $(this),
			form_id = '#'+form.attr('id'),
			url = form.attr('action'),
			form_data = new FormData(form[0]);
		clearErrors(form_id);
		swal({
			title: "Block?",
			text: "Blocking the user would prevent him from sending you association requests.\nThis action will result in deletion of all your pending and declined association requests with this user.\n Note that your current sessions with this user, if any, will still remain.",
			type: "warning",
			showCancelButton: true,
			confirmButtonColor: "#DD6B55",
			confirmButtonText: "Yes, delete it!",
			closeOnConfirm: false,
			showLoaderOnConfirm: true,
			allowOutsideClick: true,
			},
			function(){
				$.ajax({
					url: url,
					type: 'POST',
					data: form_data,
					processData: false,
					contentType: false,
					success: function(data, status, xhr){
						inProcess['create-dissociation'] = false;
						message = '\nShould you wish to associate with the user anytime in future, you\'d first need to unblock it.';
						swal({
							title: 'Success',
							text: data['message'] + message,
							type: 'success',
							allowEscapeKey: false,
							}, function(){window.location.href = '';});
					},
					error: function(xhr, status, error){
						inProcess['create-dissociation'] = false;
						if(xhr.status >= 400 && xhr.status < 500)
							swal("Oops..", "Please correct the errors.", "error");
						else if(xhr.status >= 500)
							swal("Oops..", "Sorry, an unexpected error occurred. Please try again after sometime.", "error");
						if (xhr.responseJSON['error']){
							$(form).parent().prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
						}
						var form_errors = xhr.responseJSON['errors'];
						addErrorsToForm(form_errors, form_id);
					}
				});
			});
	}

	return {
		init: function() {
			$('.delete-dissociation').tooltip();
			$('.delete-dissociation').on('click', deleteDissociation);
			$('#create-dissociation-form').on('submit', createDissociation);
		}
	}
})();
