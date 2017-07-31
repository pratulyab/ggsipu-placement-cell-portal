var Request = (function() {
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
			beforeSend: function() {
				$(form).find('button').addClass('disabled');
				showPreloader();
			},
			complete: function() {
				removePreloader();
				$(form).find('button').removeClass('disabled');
			},
			success: function(data, status, xhr){
				if (data.refresh) {
					swal({
						title: 'Success!',
						text: data.message,
						type: 'success',
						allowEscapeKey: false,
						}, function() {	(window.location.href = data.location ? data.location : '');}
					);
				} else {
					swal('Success!', data.message, 'success');
				}
			},
			error: function(xhr, status, error){
				if (xhr.responseJSON && xhr.responseJSON['error']){
					var div = $('<div class="non-field-errors"/>')
					$(form_id).prepend(div.append("<small class='error'>"+xhr.responseJSON['error']+"</small>"));
				}
				var message = (xhr.responseJSON && (xhr.responseJSON['message'] || xhr.responseJSON['error'])) ? (xhr.responseJSON['message'] || xhr.responseJSON['error']) : (xhr.status >= 500 ? 'Sorry, an unexpected error occurred. Please try again after sometime.' : 'Please correct the errors.');
				if (xhr.responseJSON && xhr.responseJSON['refresh'])
					swal({
						title: 'Error',
						text: message,
						type: 'error',
						allowEscapeKey: false,
					}, function(){window.location.href = (xhr.responseJSON['location'] ? xhr.responseJSON['location'] : '')});
				else
					swal('Error!', message, 'error');
				
				var form_errors = xhr.responseJSON['errors'];
				addErrorsToForm(form_errors, form_id);
			}
		});
	}

	function submitForm(e){
		e.preventDefault();
		handleAJAX($(this), '#' + $(this).attr('id'));
	}

	function implementRequests(e) {
		e.preventDefault();
		var a = $(this);
		var url = a.attr('href').trim().split('/').slice(1,4).join('/');
		var group = url.split('?');
		var data = group[group.length-1].split('=')[1];
		url = '/' + group[0];
		$.ajax({
			url: url,
			type: 'GET',
			data: {'ass': data},
			beforeSend: function() {
				a.addClass('disabled');
				showPreloader();
			},
			complete: function() {
				removePreloader();	
				a.removeClass('disabled');
			},
			success: function(data, status, xhr){
//				handleMultipleJquery();
				var div = a.parents('.request-content');
				div.html(data['html']);
				div.find('.change-decision').on('click', implementRequests);
				div.find('form').on('submit', submitForm);
				div.find('select').each(function(i){
					$(this).material_select();
				});
				$('#id_application_deadline_container').find('[data-form-control="date"]').each(function () {
					$(this).datetimepicker({
						format: this.dataset.dateFormat,
						timepicker: false,
						mask: false,
						scrollInput: false
					})
				});
				// To place label at its correct position
				$('#id_application_deadline').trigger('focus');
				$('.xdsoft_datetimepicker').css('display', 'none');
			}
		});
	}
	
	function getRequests(e) {
		e.preventDefault();
		var li = $(this),
			$content_div = $(li.children('a').first().attr('href'));
		li.off('click', getRequests);
		$.ajax({
			url: li.data('url'),
			type: 'GET',
			data: {},
			processData: true,
			contentType: false,
			beforeSend: function() {
				showPreloader();
			},
			complete: function() {
				removePreloader();	
			},
			success: function(data, status, xhr){
				$content_div.html(data['html']);
				$content_div.find('.card-action a').on('click', implementRequests);
				$(".delete-request").on('click', deleteMyRequest);
				$('.delete-request').tooltip({'delay':50, 'tooltip': 'Delete request', 'position': 'bottom'});
			},
			error: function(xhr, status, error){
				$content_div.html('Error Occurred');
			}
		});
	}

	function deleteMyRequest(e){
		var url = $(this).attr('href');
		e.preventDefault();
		swal({
			title: "Are you sure?",
			text: "This action is irreversible. Your action might be recorded for reference purposes.",
			type: "warning",
			showCancelButton: true,
			confirmButtonColor: "#DD6B55",
			confirmButtonText: "Yes, delete it!",
			closeOnConfirm: false,
			showLoaderOnConfirm: true,
			allowEscapeKey: false,
			allowOutsideClick: false,
			},
			function(){
				$.ajax({
					url: url,
					type: 'POST',
					data: {'csrfmiddlewaretoken': $('input[name = csrfmiddlewaretoken]').first().val()},
					success: function(data, status, xhr){
						swal({
							title: "Deleted!",
							text: "The request has been deleted.",
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


	return {
		init: function(){
			// For initializing
			$("#request").on('click', getRequests);
			$("#myrequest").on('click', getRequests);
			$("#request").on('reload', getRequests);
			$("#myrequest").on('reload', getRequests);
			// mobile
			$("#m-request").on('click', getRequests);
			$("#m-myrequest").on('click', getRequests);
			$("#m-request").on('reload', getRequests);
			$("#m-myrequest").on('reload', getRequests);
		}
	};
})();
