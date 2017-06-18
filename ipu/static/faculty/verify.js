var VerifyStu = (function() {
	var tabs;
	'use strict';

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

	function reset_verification_forms(){
		console.log('reset');
		$('#profile-div').html('<h4 class="center-align" style="color: goldenrod">Student Profile</h4>');
		$('#qual-div').html('<h4 class="center-align" style="color: goldenrod">Student Qualifications</h4>');
		$('#id_enroll').off('input');
//					$('#delete-btn').off('click');
		$('#delete-div form').off('submit');
		tabs[0].click();
	}

	function getEnrollment(e) {
		e.preventDefault();
		clearErrors('#enrollment-div');
		reset_verification_forms();
		var form = $(this);
		var url = form.attr('action');
		var form_data = new FormData(form[0]);
		$.ajax({
			url: url,
			type: 'POST',
			data: form_data, 
			processData: false,
			contentType: false,
			success: function(data, status, xhr){
				handleMultipleJquery();
				data = data.split('<<<>>>');
				$('#profile-div').append(data[0]);
				$('#qual-div').append(data[1]);
				$('#id_enroll').on('input', reset_verification_forms);
				$('#profile-form').on('submit', updateProfile);
				$('#qual-form').on('submit', updateQual);
//				$('#delete-btn').on('click', delete_button);
				$('#delete-div form').on('submit', delete_button);
//				console.log($('body').find('ul'));

				// Trigerring next tab
				tabs[1].click()
			},
			error: function(xhr, status, error){
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrors(form_errors, '#enroll-form');
			}
		});
	}

	function updateProfile(e) {
		e.preventDefault();
		clearErrors('#profile-div');
		$('#profile-div .success').remove();
		var form = $(this);
		var url = form.attr('action');
		var form_data = new FormData(form[0]);
		form.off('submit');
		$.ajax({
			type: 'POST',
			url: url,
			data: form_data,
			processData: false,
			contentType: false,
			success: function(data, status, xhr){
				handleMultipleJquery();
				$('#profile-div').html(data);
				// because new html has been added
				$('#profile-form').on('submit', updateProfile);
				window.scrollTo(0,0);
//				tabs[2].click();
			},
			error: function(xhr, status, error){
				var error_msg = xhr.responseJSON['error']
				if(error_msg){
					$('#profile-div').prepend($('<small class="error">' + error_msg + '</small>'));
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrors(form_errors, '#profile-form');
				$('#profile-form').on('submit', updateProfile);
			}
		});
	}

	function updateQual(e) {
		e.preventDefault();
		clearErrors('#qual-div');
		var form = $(this);
		var url = form.attr('action');
		var form_data = new FormData(form[0]);
		form.off('submit');
		$.ajax({
			url: url,
			type: 'POST',
			data: form_data,
			contentType: false,
			processData: false,
			success: function(data, status, xhr){
				$('#qual-div').html(data);
				$('#qual-form').on('submit', updateQual);
				window.scrollTo(0,0);
//				tabs[1].click();
			},
			error: function(xhr, status, error){
				var error_msg = xhr.responseJSON['error']
				if(error_msg){
					$('#profile-div').prepend($('<small class="error">' + error_msg + '</small>'));
				}
				var form_errors = xhr.responseJSON['errors'];
				addErrors(form_errors, '#qual-form');
				$('#qual-form').on('submit', updateQual);
			}
		});
	}

	function delete_button(e) {
		e.preventDefault();
		var form = $(this);
		var form_data = new FormData(form[0]);
		swal({
			title: "Are you sure?",
			text: "This action is irreversible. Your action will be recorded for reference purposes.",
			type: "warning",
			showCancelButton: true,
			confirmButtonColor: "#DD6B55",
			confirmButtonText: "Yes, delete student!",
			closeOnConfirm: false,
			showLoaderOnConfirm: true,
			allowEscapeKey: false,
			allowOutsideClick: true,
			},
			function(){
				$.ajax({
					url: '/student/delete/',
					type: 'POST',
					data: form_data,
					contentType: false,
					processData: false,
					success: function(data, xhr, status){
						swal({
							title: "Deleted!",
							text: "The student has been deleted.",
							type: "success",
							allowEscapeKey: false,
							},function(){window.location.href = '';});
					},
					error: function(xhr, status, error){
						if (xhr.status >= 400 && xhr.status < 500) {
							addErrors(xhr.responseJSON('error'), '#delete-div');
							var error_msg = xhr.responseJSON['error'] ? xhr.responseJSON['error'] : "Error Occurred.";
							swal("Error!", error_msg, "error");
						} else if (xhr.status > 500) {
							swal("Oops..", "Sorry, an unexpected error occurred. Please try again after sometime.", "error");
						}
					}
				});
			}
		);
	}
	return {
		init: function(){
			$('#enroll-form').submit(getEnrollment);
			$('#delete-div form').on('submit', function(e){e.preventDefault();});
			tabs = $('#student-div .vertical-tabs .tabs > li a');
		}
	};
})();
