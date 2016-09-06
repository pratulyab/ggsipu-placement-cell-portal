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
			error: function(status, xhr, error){
				var loc = xhr.responseJSON['location'];
				if (loc){
					location.href = loc;
					return;
				}
				div.append($('<p class="error">' + "Error occurred. Please try again later." + '</p>'))
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
				var render_div = $('<div id="opportunities"/>');
				render_div.html($('<h4 class="center" style="color: #1c262f;">' + "Jobs" + '</h4>'));
				render_div.append(data['jobs']);
				render_div.append('<h4 class="center" style="color: #1c262f;">' + "Internships" + '</h4>');
				render_div.append(data['internships']);
				div.html(render_div);
				$(render_div).find('img.activator').removeAttr('src');
				$(render_div).find('a.change-enrollment').on('click', changeEnrollment);
			},
			error: function(status, xhr, error) {
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
