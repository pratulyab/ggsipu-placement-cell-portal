var ManageFaculty = (function() {
	var inProcess = {
		'perms': false,
	}

	function deleteFaculty(e){
		e.preventDefault();
		var url = $(this).attr('href');
		swal({
			title: "Are you sure?",
			text: "This action is irreversible. Your action will be recorded for reference purposes.",
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
					data: {'csrfmiddlewaretoken': $('#view-faculty-div').find('input[name = csrfmiddlewaretoken]').val()},
					success: function(data, status, xhr){
						swal({
							title: "Deleted!",
							text: "The faculty has been deleted.",
							type: "success",
							allowEscapeKey: false,
							},function(){window.location.href = '';}
						);
					},
					error: function(xhr, status, error){
						var error_msg = xhr.responseJSON['error'] ? xhr.responseJSON['error'] : "Error Occurred.";
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

	function submitForm(e){
		e.preventDefault();
		if (inProcess['perms'])
			return;
		var	form = $(this),
			form_id = '#'+form.attr('id'),
			url = form.attr('action'),
			form_data = new FormData(form[0]);
		inProcess['perms'] = true;
		clearErrors(form_id);
		$.ajax({
			url: url,
			type: 'POST',
			data: form_data,
			processData: false,
			contentType: false,
			success: function(data, status, xhr){
				inProcess['perms'] = false;
				swal('Success', data['success_msg'], 'success');
			},
			error: function(xhr, status, error){
				inProcess['perms'] = false;
				if(xhr.status >= 400 && xhr.status < 500)
					swal("Oops..", "An error occurred", "error");
				else if(xhr.status >= 500)
					swal("Oops..", "Sorry, an unexpected error occurred. Please try again after sometime.", "error");
				if (xhr.responseJSON['error']){
					$(form).parent().prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
			}
		});
	}

	function getPermsForm(e){
		e.preventDefault();
		var	form = $(this),
			form_id = '#'+form.attr('id'),
			url = form.attr('action'),
			div = $('#faculty-perms-div'),
			faculty_field = $('#choose-faculty-form').find('#id_faculty'),
			chosen_hashid = $(faculty_field.children()[faculty_field.prop('selectedIndex')]).attr('value');
		clearErrors(form_id);
		url += chosen_hashid + '/';
		$.ajax({
			url: url,
			type: 'GET',
			data: {},
			success: function(data, status, xhr){
				var $render_div = $('#edit-faculty-perms-div');
				$render_div.html($(data['html']));
				faculty_field.on('change', function(e){
					$('#edit-faculty-perms-div').html('');
				});
				$render_div.find('#id_groups').material_select();
				$('#edit-faculty-perms-form').on('submit', submitForm);
			},
			error: function(xhr, status, error){
				if (xhr.responseJSON['error']){
					$(form).parent().prepend($('<small class="error">'+xhr.responseJSON['error']+'</small>'))
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
			}
		});
	}
	
	return {
		init: function() {
			$('.delete-faculty').tooltip();
			$('.delete-faculty').on('click', deleteFaculty);
			$('#choose-faculty-form').on('submit', getPermsForm);
		}
	}
})();
