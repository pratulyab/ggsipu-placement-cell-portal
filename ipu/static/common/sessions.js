var Session = (function() {
	"use strict";
	var sessionCounter = 0;
	/*
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
	*/
/*
	function generateExcel(e) {
		e.preventDefault();
		var a = $(this);
		var li = a.parent();
		var sess = li.data('sess');
		var url = a.attr('href');
		$.ajax({
			url: url,
			type: 'GET',
			async: true,
			data: {'sess': sess},
			success: function(data, status, xhr){
				window.location = data;
			},
			error: function(status, xhr, error){;}
		});
	}
*/
	function getSessions() {
		sessionCounter++;
		if (sessionCounter >= 10){
			location.href = '';
			return;
		}
		var li = $(this);
		var div = $('#sessions');
		$.ajax({
			url: '/recruitment/mysessions/',
			type: 'GET',
			data: {},
			success: function(data, status, xhr){
//				handleMultipleJquery();
				var loc = data['location'];
				if (loc){
					location.href = loc;
				}
				div.html(data['html']);
//				$('.excel').on('click', generateExcel);
			},
			error: function(status, xhr, error){
				div.html($('<p>' + "Sorry, couldn't retrieve your sessions.<br><br>" + '</p>'));
				if (xhr['error']){
					var p = $('<p/>');
					p.html(xhr['error']);
				}
			}
		});
	}

	return {
		init: function() {
			var li = $('#session');
			li.on('click', getSessions);
		}
	};
})();
