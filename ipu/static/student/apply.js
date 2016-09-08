var Apply = (function() {
	"use strict";

	function changeEnrollment(e){
		e.preventDefault();
		var a = $(this);
		var url = a.attr('href');
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
					a.html(p);
				}
				else{
					p.html("<b>Error occurred. Please try again later.</b>");
					a.html(p);
				}
				a.off();
				a.on('click', function(e){e.preventDefault();});
			}
		});
	}
	
	function getOpportunities(e) {
		var div = $('#companies');
		$.ajax({
			url: '/student/view_companies/',
			type: 'GET',
			data: {},
			success: function(data, status, xhr) {
				var loc = data['location'];
				if (loc){
					location.href = loc;
					return;
				}
				var form = data['form'];
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
				$('.toc-wrapper').pushpin({top: top, offset:top});
				$('.scrollspy').scrollSpy();
				$('.nested-scrollspy').scrollSpy();
			},
			error: function(xhr, status, error) {
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				div.append($('<p class="error">' + "Error occurred. Please try again later." + '</p>'))
			}
		});
	}
	
	return {
		init: function() {
			$('#apply').on('click', getOpportunities);
		}
	};
})();
