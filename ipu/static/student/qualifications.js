var Qual = (function() {
	var tenth = null,
		twelfth = null,
		grad = null;

	function handle_AJAX($button, data){
		$('#error-box').find('.errors').empty();
		swal({
			title: "Submit?",
			text: "By submitting the qualifications, you 'Agree' that you are solely responsible for the correctness of information you've provided, and the University holds the right to take any necessary actions should any irregularities be found.",
			type: "warning",
			showCancelButton: true,
			confirmButtonColor: "#DD6B55",
			confirmButtonText: "Yes, I Agree",
			closeOnConfirm: false,
			showLoaderOnConfirm: true,
			allowEscapeKey: false,
			allowOutsideClick: false,
			},
			function(){
				$.ajax({
					url: $button.attr('action'),
					type: $button.attr('method'),
					data: data,
					processData: false,
					contentType: false,
					success: function(data, status, xhr){
						if (data.refresh){	
							swal({
								title: "Success!",
								text: "Your qualifications have been saved.",
								type: "success",
								allowEscapeKey: false,
								},function(){
									var location = data.location ? data.location : '';
									window.location.href = location;
								}
							);
						} else {
							swal("Success!", "Your Qualifications have been saved.", 'success');
						}
					},
					error: function(xhr, status, error){
						if(xhr.status >= 400 && xhr.status < 500)
							swal('Error', "Please correct the errors as indicated in the error box.", 'error');
						else if(xhr.status >= 500)
							swal("Oops..", "Sorry, an unexpected error occurred. Please try again after sometime.", "error");
						var ul = $('#error-box').find('ul');
						var errors = xhr.responseJSON['errors'];
		//				console.log(errors);
						var type = xhr.responseJSON['type'];
						if (type == 'score'){
							for (var field_name in errors) {
								var $li = $('<li class="blue-text flow-text"/>');
								var text = field_name;
								if (field_name == 'tenth')
									text = '10th Qualifications:'
								else if (field_name == 'twelfth')
									text = '12th Qualifications:'
								$li.text(text);
								for (var i=0; i<errors[field_name].length; i++) {
									var each = errors[field_name][i];
									for (var key in each) {
										for(var message of each[key]){
											$li.append($('<li class="red-text left-align">'+'<span class="purple-text">' + key +' </span>' +message+'</li>'));
										}
									}
									ul.append($li);
								}
							}
						} else if (type == 'board'){
							for (var key in errors) {
								var message = errors[key];
								var $li = $('<li class="blue-text flow-text"/>');
								$li.text(key);
								$li.append($('<li class="red-text left-align">'+message+'</li>'));
								ul.append($li);
							}
						} else {
							for (var key in errors){
								var $li = $('<li class="blue-text flow-text"/>');
								$li.text(key);
								for(var message of errors[key]){
									$li.append($('<li class="red-text left-align">'+message+'</li>'));
								}
								ul.append($li);
							}
						}
					}
				});
			}
		); //end of swal
	}

	function appendToFormData(form_data, serialized_data){
		for (var i=0; i<serialized_data.length; i++){
			var pair = serialized_data[i].split('=');
			form_data.append(pair[0], pair[1]);
		}
		return form_data;
	}

	function submitForms(e){
		e.preventDefault();
		var is_cgpa = $('#tenth-toggle-form').find('#choose-cgpa-form')[0].checked ? true : false,
			which_tenth_form = is_cgpa ? tenth.cgpa_form : tenth.score_form;
		which_tenth_form = $(which_tenth_form);
		var form_data = new FormData();
		form_data.append('csrfmiddlewaretoken', $('input[name = csrfmiddlewaretoken]').val());
		form_data.append('is_cgpa', (is_cgpa ? 'cgpa' : ''));
		
		/* Tenth Qual */
		var serialized_data = which_tenth_form.serialize().split('&');
		form_data = appendToFormData(form_data, serialized_data);
		/* */

		/* Twelfth Qual */
		serialized_data = twelfth.find('#twelfth-scores-marksheet-form').serialize().split('&');
		form_data = appendToFormData(form_data, serialized_data);
		/* */
		
		/* Grad Qual */
		serialized_data = grad.find('form').serialize().split('&');
		form_data = appendToFormData(form_data, serialized_data);
		/* */
		handle_AJAX($(this), form_data);
	}
	
	return {
		init: function() {
			tenth = {
				'tenth': '#tenth',
				'score': '#tenth-scores-marksheet-form-div',
				'cgpa': '#tenth-cgpa-marksheet-form-div',
				'score_form': '#tenth-scores-marksheet-form',
				'cgpa_form': '#tenth-cgpa-marksheet-form'
			};
			twelfth = $('#twelfth');
			grad = $('#graduation');
			$(tenth.tenth).find('div[id*="marksheet-form-div"]').hide();
			$('#tenth-toggle-form').find('#choose-cgpa-form').on('change', function(e){
						$(tenth.score).hide();
						$(tenth.cgpa).show();
					});
			$('#tenth-toggle-form').find('#choose-scores-marksheet-form').on('change', function(e){
						$(tenth.cgpa).hide();
						$(tenth.score).show();
					});

			var toggle_subject_fillers = $('[id$="toggle_subject_filler"]');
			toggle_subject_fillers.on('change', function(){
				var $input = $(this);
				if ($input[0].checked)
					$input.parents('div.section').next().show();
				else
					$input.parents('div.section').next().hide();
			});
			toggle_subject_fillers.trigger('change');
			$('h5').addClass('flow-text');
			$('.continue-btn').tooltip();
			$('#submit-forms-btn').on('click', submitForms);
		}
	}
})();
