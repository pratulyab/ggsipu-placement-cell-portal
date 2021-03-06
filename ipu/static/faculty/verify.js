var VerifyStu = (function() {
	var tabs, $scoreModal;
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
		$(el).find('.has-error').removeClass('has-error');
	}

	function addErrors(form_errors, el, prefix=''){
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

	function reset_verification_forms(){
		$('#profile-div').html('<h4 class="center-align" style="color: lightcoral">Student Profile</h4>');
		$('#tenth-div').html('<h4 class="center-align" style="color: lightcoral">10th Qualifications</h4>');
		$('#twelfth-div').html('<h4 class="center-align" style="color: lightcoral">12th Qualifications</h4>');
		$('#grad-div').html('<h4 class="center-align" style="color: lightcoral">Graduation Qualifications</h4>');
		$('#id_enroll').off('input');
//					$('#delete-btn').off('click');
		$('#delete-div form').off('submit');
		tabs[0].click();
	}

	function updateScore(e) {
		var url = $(this).data('url'); // this == modal button
		var $form = $scoreModal.find('form');
		var form_data = new FormData($form[0]);
		$.ajax({
			url: url,
			type: 'POST',
			data: form_data,
			processData: false,
			contentType: false,
			beforeSend: function(){
				showPreloader();
			},
			complete: function(){
				removePreloader();
			},
			success: function(data, status, xhr){
				swal('Success', data.message, 'success');

				var $content = $(data.form);
				var content_div = $('#'+$content.attr('id'));
				content_div.replaceWith($content);
				$content.find('select').material_select();
				$content.find('i.edit-icon').tooltip({tooltip: 'Edit', delay: '25ms', position: 'right'})
				$content.find('i.edit-icon').on('click', getScore);
				$('[id$="-board-form"]').on('submit', submitForm);
				$scoreModal.modal({
					ready: function(modal,trigger){
						modal.find('.score-submit-button').on('click', updateScore);
					},
					complete: function() { $scoreModal.find('.score-submit-button').off('click', updateScore); }
				});
			},
			error: function(xhr, status, error){
				if (xhr.status<500){
					var message = xhr.responseJSON ? xhr.responseJSON['error'] : 'Error occurred';
					swal('Error!', message, 'error');
				} else {
					swal('Error!', 'Sorry, an unexpected error occurred. Please try again after sometime.', 'error');
				}
			}
		});

	}

	function getScore(e) {
		e.preventDefault();
		var url = $(this).data('url');
		$.ajax({
			url: url,
			type: 'GET',
			data: {},
			processData: false,
			contentType: false,
			beforeSend: function(){
				showPreloader();
			},
			complete: function(){
				removePreloader();
			},
			success: function(data, status, xhr){
				$scoreModal.find('.modal-content').html(data.form);
				$scoreModal.find('select').material_select();

				var toggle_subject_fillers = $scoreModal.find('[id$="toggle_subject_filler"]');
				toggle_subject_fillers.on('change', function(){
					var $input = $(this);
					if ($input[0].checked)
						$input.parents('div.section').next().show();
					else
						$input.parents('div.section').next().hide();
				});
				toggle_subject_fillers.trigger('change');
				$scoreModal.modal('open');
				$scoreModal.find('.score-submit-button').data('url', url);
			},
			error: function(xhr, status, error){
				if (xhr.status<500){
					var message = xhr.responseJSON ? xhr.responseJSON['error'] : 'Error occurred';
					swal('Error!', message, 'error');
				} else {
					swal('Error!', 'Sorry, an unexpected error occurred. Please try again after sometime.', 'error');
				}
			}
		});
	}

	function verify(e){ /* Same as submitForm but with swal warning */
		e.preventDefault();
		var form = $(this);
		clearErrors('#'+form.attr('id'));
		var form_data = new FormData(form[0]);

		swal({
			title: "Are you sure?",
			text: "You are about to verify student. This will allow the student to access the portal. Your activity will be logged for reference purposes.",
			type: "warning",
			showCancelButton: true,
			confirmButtonColor: "#DD6B55",
			confirmButtonText: "Yes, verify!",
			cancelButtonText: "No",
			closeOnConfirm: false,
			closeOnCancel: false
			}, function(){
					$.ajax({
						url: form.attr('action'),
						type: form.attr('method'),
						data: form_data,
						processData: false,
						contentType: false,
						beforeSend: function(){
							showPreloader();
						},
						complete: function(){
							removePreloader();
						},
						success: function(data, status, xhr) {
							swal({
								title: 'Verified!',
								text: (data.message ? data.message : "Student has been successfully verified."),
								type: 'success',
								allowEscapeKey: false,
								allowOutsideClick: false,
								},
								reset_verification_forms
							);
						},
						error: function(xhr, status, error) {
							if (xhr.responseJSON && xhr.responseJSON['errors']){
								addErrors(xhr.responseJSON['errors'], '#'+form.attr('id'), xhr.responseJSON['prefix']);
							}
							if (xhr.status<500){
								var message = xhr.responseJSON ? xhr.responseJSON['error'] : 'Error occurred';
								swal('Error!', message, 'error');
							} else {
								swal('Error!', 'Sorry, an unexpected error occurred. Please try again after sometime.', 'error');
							}
						}
					});
				}
			);
	}

	function submitForm(e){
		e.preventDefault();
		var form = $(this);
		clearErrors('#'+form.attr('id'));
		var form_data = new FormData(form[0]);

		$.ajax({
			url: form.attr('action'),
			type: form.attr('method'),
			data: form_data,
			processData: false,
			contentType: false,
			beforeSend: function(){
				showPreloader();
			},
			complete: function(){
				removePreloader();
			},
			success: function(data, status, xhr) {
				swal('Success', data.message ? data.message : "Changes have been saved", 'success');
			},
			error: function(xhr, status, error) {
				if (xhr.responseJSON && xhr.responseJSON['errors']){
					addErrors(xhr.responseJSON['errors'], '#'+form.attr('id'), xhr.responseJSON['prefix']);
				}
				if (xhr.status<500){
					var message = xhr.responseJSON ? xhr.responseJSON['error'] : 'Error occurred';
					swal('Error!', message, 'error');
				} else {
					swal('Error!', 'Sorry, an unexpected error occurred. Please try again after sometime.', 'error');
				}
			}
		});
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
			beforeSend: function() {
				form.find('button').addClass('disabled');
				showPreloader();
			},
			complete: function() {
				form.find('button').removeClass('disabled');
				removePreloader();	
			},
			success: function(data, status, xhr){
				handleMultipleJquery(); // required
				$('#profile-div').append(data.profile)
				$('#tenth-div').append(data.tenth);
				$('#twelfth-div').append(data.twelfth);
				$('#grad-div').append(data.grad);

				$('#cgpa-form').on('submit', submitForm);
				$('[id$="-board-form"]').on('submit', submitForm);
				$('#grad-form').on('submit', verify);
				$('#profile-form').on('submit', submitForm);

				$('#tab-content').find('select').material_select();
				$('i.edit-icon').tooltip({tooltip: 'Edit', delay: '25ms', position: 'right'})
				$('i.edit-icon').on('click', getScore);
				$('#id_enroll').on('input', reset_verification_forms);
				$('#delete-div form').on('submit', delete_button);
				$scoreModal = $('#score-modal');
				$scoreModal.modal({
					ready: function(modal,trigger){
						modal.find('.score-submit-button').on('click', updateScore);
					},
					complete: function() { $scoreModal.find('.score-submit-button').off('click', updateScore); }
				});
				$('#id_is_barred').on('change', function(){
					var title = $(this)[0].checked ? "Bar?" : "Unbar?";
					var message = "Changing student's barred status is a highly sensitive decision. Your activity will be logged for reference purposes."
					swal(title, message, 'warning');
				});
				$('i.left-right').tooltip();
//				console.log($('body').find('ul'));
				if (data['graduated']) {
					$('#profile-div').prepend('<h6 class="blue-text center-align">This student has graduated. Contact admin if it is required to change student\'s graduation status.</h6>');
				}
				if (data['verified']) {
					$('#profile-div').prepend('<h4 class="teal-text center-align">(Verified)</h4>');
				}
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
/*
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
*/
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
			allowOutsideClick: false,
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
							addErrors(xhr.responseJSON['errors'], '#delete-div');
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
