var Paygrade = (function() {
		
	function clearErrors(el){
		$(el + ' .non-field-errors').remove();
		$(el + ' .errors').remove();
		$(el + ' .input-field').removeClass('has-error');
		$(el + ' .input-field input').removeClass('invalid');
	}

	function addErrors(form_errors, el){
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

	function handle_paygrade(e) {
		e.preventDefault();
		var form = $(this);
		var form_data = new FormData(form[0]);
		swal({
			title: "Are you sure?",
			text: "You won't be able eligible for companies offering salary lesser than the salary you choose. Also, you won't be able to change this again",
			type: "warning",
			showCancelButton: true,
			confirmButtonColor: "#DD6B55",
			confirmButtonText: "Yes, continue!",
			closeOnConfirm: false,
			showLoaderOnConfirm: true,
			allowEscapeKey: false,
			allowOutsideClick: true,
			},
			function(){
				clearErrors('#paygrade-form-div');
				$.ajax({
					url: form.attr('action'),
					type: 'POST',
					data: form_data,
					contentType: false,
					processData: false,
					success: function(data, xhr, status){
						swal({
							title: "Updated!",
							text: "Your salary expectation has been saved. For any future discrepancies regarding this, contact your college.",
							type: "success",
							allowEscapeKey: false,
							},function(){window.location.href = '';});
					},
					error: function(xhr, status, error){
						if (xhr.status >= 400 && xhr.status < 500) {
							addErrors(xhr.responseJSON['errors'], '#paygrade-form');
							var error_msg = xhr.responseJSON['error'] ? xhr.responseJSON['error'] : "Error Occurred.";
							swal("Error!", error_msg, "error");
						} else if (xhr.status > 500) {
							swal("Oops..", "Sorry, an unexpected error occurred. Please try again after sometime.", "error");
						}
					}
				});
		});
	}
	
	return {
		init: function() {
			$('#paygrade-form').on('submit', handle_paygrade);
		}
	}
})();
