var Apply = (function() {
	"use strict";

	var applicationCounter = 0,
		opporCounter = 0,
		initialTimeout = null;

	function changeEnrollment(e){
		e.preventDefault();
		applicationCounter++;
		if (applicationCounter >= 10){
			location.href = '';
			return;
		}
		var a = $(this);
		var url = a.attr('href');
		swal({
			title: a.html() + '?',
			text: "You can undo your action within " + a.data('timeleft'),
			type: "warning",
			showCancelButton: true,
			closeOnConfirm: false,
			allowEscapeKey: true,
//			allowOutsideClick: true,
			showLoaderOnConfirm: true, 
			},
			function(){
//				setTimeout(function(){swal("Ajax request finished!");}, 2000);});
		$.ajax({
			url: url,
			type: 'GET',
			data: {},
			success: function(data, status, xhr){
				var loc = data['location'];
				if (loc){
					location.href = loc;
					return;
				}
				var now_enrolled = data['enrolled'];
				a.html(now_enrolled ? "Withdraw Application" : "Apply");
				swal(now_enrolled ? "Applied Successfully" : "Application Withdrawn Successfully", '', "success");
			},
			error: function(xhr, status, error){
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				var p = $('<p class="error"/>')
				var error = xhr.responseJSON['error'];
				if (error){
					p.html('<b>' + error + '</b>');
					p.css('cursor', 'default');
					a.html(p);
					swal("Oops!", error, "error");
				}
				else{
					p.html("<b>Error occurred. Please try again later.</b>");
					a.html(p);
					swal("Oops...", "Sorry, an unintentional error occurred. Please try again after sometime.", "error");
				}
				a.off();
				a.on('click', function(e){e.preventDefault();});
			},
			
		});
	});
	}
	
	function getOpportunities(e) {
//		clearTimeout(initialTimeout);
		var div = $('#companies');
		opporCounter++;
		if (opporCounter >= 10){
			location.href = '';
			return;
		}
//		swal({
//			title: "Retrieve the companies list?",
//			text: "",
//			type: "info",
//			showCancelButton: true,
//			allowEscapeKey: true,
////			allowOutsideClick: true,
//			confirmButtonText: "Yes!",
//			cancelButtonText: "No, Thanks!",
//			closeOnConfirm: false,
//			showLoaderOnConfirm: true,
//			closeOnCancel: false
//			}, function(isConfirm){
//				if (isConfirm) {
					// Send AJAX request
					$.ajax({
						url: '/student/view_companies/',
						type: 'GET',
						data: {},
						beforeSend: function() {
							showPreloader();
						},
						complete: function() {
							removePreloader();
						},
						success: function(data, status, xhr) {
							var loc = data['location'];
							if (loc){
								location.href = loc;
								return;
							}
//							swal("Success", '', "success");
							var bar = data['barred'];
							if (bar){
								var h1 = $('<h1 class="center flow-text teal-text text-accent-4"/>')
								h1.html('<b>' + bar + '</b>');
								div.html(h1);
								return;
							}
							var form = data['form'];
			//				var h3 = $('<h3 class="center flow-text teal-text text-accent-4"/>')
			//				h3.html('You wouldn\'t be able to view/apply to companies offering lesser salary than your minimum expected salary')
							if (form){
								var form_div = $('<div id="paygrade-form-div" class="col s12"/>');
								form_div.html(form);
								div.html(form_div);
								$(div).find('select').material_select();
								return;
							}
							var render_div = $('<div id="opportunities" class="col s12 m9 l10"/>');
							render_div.append(data['jobs']);
							render_div.append(data['internships']);
							div.html(render_div);
							$(render_div).find('img.activator[src="#"]').removeAttr('src');
							$(render_div).find('a.change-enrollment').on('click', changeEnrollment);
							var pushpin = '<div class="col hide-on-small-only m3 l2"><div class="toc-wrapper"><ul class="table-of-contents"><li><a href="#jobs">Jobs</a><ul class="nested-pushpin"><li><a href="#enrolled-jobs">Enrolled</a></li><li><a href="#unenrolled-jobs">Un-enrolled</a></li></ul></li><li><a href="#internships">Internships</a><ul class="nested-pushpin"><li><a href="#enrolled-internships">Enrolled</a></li><li><a href="#unenrolled-internships">Un-enrolled</a></li></ul></li></ul></div>';
							var parsedPushpin = $.parseHTML(pushpin);
							div.append(parsedPushpin);
							var top = div.offset().top;
							$('.toc-wrapper').pushpin({offset:top});
							$('.scrollspy').scrollSpy();
							$('.nested-scrollspy').scrollSpy();
						},
						error: function(xhr, status, error) {
							var loc = xhr.responseJSON['location'];
							if (loc){
								location.href = loc;
								return;
							}
							swal("Oops...", "Sorry, an unintentional error occurred. Please try again after sometime.", "error");
							div.append($('<p class="error">' + "Error occurred. Please try again later." + '</p>'))
						}
					}); // end of $.ajax
//				} // end of if isConfirm
//				else
//					swal("Alright!", "To retrieve/refresh the list any time, just click the 'Companies Visiting' tab.");
//			}
//		);
	}
	
	return {
		init: function() {
			$('#apply').on({
//				'click': getOpportunities,
				'reload': getOpportunities,
			});
			$('#apply').trigger('reload');
			
//			initialTimeout = setTimeout( function(){
//				$('li#apply').click();
//			}, 2000);
		}
	};
})();
