var Session = (function() {
	"use strict";
	var sessionCounter = 0,
		inProcess = {
			'nss': false,
			'sess': false,
			'filter_sessions': false,
			'filter_dsessions': false
		};

	
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

	function notifySessionStudents(e) {
		e.preventDefault();
		var $envelope = $(this),
			$lightbox = $('#light3'),
			url = $envelope.attr('href'),
			form = $lightbox.find('#notify-session-students-form');
		$lightbox.css('display', 'flex');
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
				beforeSend: function() {
					showPreloader();
					form.find('button').addClass('disabled');
				},
				complete: function() {
					removePreloader();
					form.find('button').removeClass('disabled');
				},
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
		if (inProcess['sess'])
			return;
		sessionCounter++;
		if (sessionCounter >= 10){
			location.href = '';
			return;
		}
		var li = $(this);
		var div = $('#sessions_div');
		inProcess['sess'] = true;
		$.ajax({
			url: '/recruitment/mysessions/',
			type: 'GET',
			data: {},
			beforeSend: function() {
				showPreloader();
			},
			complete: function() {
				removePreloader();
			},
			success: function(data, status, xhr){
//				handleMultipleJquery();
				var loc = data['location'];
				if (loc){
					location.href = loc;
				}
				div.html(data['html']);
				div.find('a.envelope').on('click', notifySessionStudents);
				inProcess['sess'] = false;	
//				$('.excel').on('click', generateExcel);
			},
			error: function(status, xhr, error){
				div.html($('<p class="red-text center-align">' + "Sorry, couldn't retrieve your sessions.<br><br>" + '</p>'));
				if (xhr['error']){
					var p = $('<p/>');
					p.html(xhr['error']);
				}
				inProcess['sess'] = false;
			}
		});
	}

	function filterSessions(e) {
		e.preventDefault();
		var form = $(this),
			div_id = form.data('filter'),
			$div = $('#' + div_id),
			form_data = new FormData(form[0]),
			semaphore = 'filter_' + div_id;
		if (inProcess[semaphore]){
			console.log('returned');
			return
		}
		else
			inProcess[semaphore] = true
		$('#filter-preloader').html($('<div class="progress"><div class="indeterminate"></div></div>'));
		$('.session-filter-forms-sideNav').sideNav('hide');
		$.ajax({
			url: form.attr('action'),
			type: 'POST',
			data: form_data,
			processData: false,
			contentType: false,
			beforeSend: function() {
				showPreloader();
				form.find('button').addClass('disabled');
			},
			complete: function() {
				removePreloader();
				form.find('button').removeClass('disabled');
			},
			success: function(data, status, xhr){
				$('#filter-preloader').empty();
				if (!$div.length)
					$div = $('#sessions_div');
				$div.html(data['html']);
				Materialize.toast($('<span class="flow-text green-text" />').html('Filtered successfully!').css('fontWeight', 'bold'), 5000);
				inProcess[semaphore] = false;
			},
			error: function(xhr, status, error){
				$('#filter-preloader').empty();
				Materialize.toast($('<span class="flow-text red-text" />').html('Error occurred while filtering.').css('fontWeight', 'bold'), 5000);
				inProcess[semaphore] = false;
			}
		});
	}

	return {
		init: function() {
			var li = $('#session');
			li.on('click', getSessions);
			$('.session-filter-form').on('submit', filterSessions);
		}
	};
})();
