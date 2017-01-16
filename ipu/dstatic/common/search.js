var Search = (function() {
	'use strict';

	function handleTechProfiles(span, username){
		var accordion = $(span).find('ul.collapsible li');
		if (!accordion.length)
			return;
		$(accordion).each(function(i, li){
			li = $(li);
			li.find('.collapsible-header').on('click', function(){
				var platform = li.attr('id');
				var body = li.find('.collapsible-body');
				body.html("Fetching student's profile...");
				$.ajax({
					url: '/student/coder/',
					type: 'GET',
					data: {'platform': platform, 'username': username},
					success: function(data, status, xhr){
						body.html(data['html']);
					},
					error: function(status, xhr, error){
						body.html('Error Occurred.');
					}
				})
			});
		});
	}

	function displayProfile(e){
		var a = $(this);
		var li = a.parent();
		$(li.parent()[0]).find('li').removeClass('tooltip');
		$('span.tooltiptext').remove();
		var url = a.attr('href');
		var span = $('<span class="tooltiptext"/>');
		$.ajax({
			url: url,
			type: 'GET',
			success: function(data, status, xhr){
				li.addClass('tooltip');
				span.html(data['card-html']);
				var username = url.split('/');
				username = username[username.length-2];
				handleTechProfiles(span, username);
				li.append(span);
				span.on('mouseleave', function(e){
					span.remove();
					li.removeClass('tooltip');
				});
			}
		});
	}

	function displayResults(data){
		if (data['location']){
			location.href = location;
			return;
		}
		var ul = $('#search-line #results');
		if (!ul){
			ul = $('<ul id="results"/>');
			$('form#search-line').append(ul);
		}
		ul.empty();
		
		if (!data['success']){
			var p = $('<p>' + data['message'] + '</p>');
			p.css('color', '#7d97ad');
			ul.append(p);
		}
		else{
			var results = data['result'];
			for (var i=0; i<results.length; i++){
				var item = results[i];
				var li = $('<li class="search-item"/>');
				var a = $('<a>' + item['name'] + '</a>');
				a.attr('href', item['url']);
				a.on('mouseenter', displayProfile);
				a.css('color','#02b3e4');
				li.append(a);
				ul.append(li);
			}
		}
	}
	
	function search(e) {
		var query = $(this).val();
		$('#search-line #results').empty();
		$.ajax({
			url: '/search/',
			type: 'GET',
			data: {'query': query},
			success: function(data, status, xhr){
				displayResults(data);
			}
		});
	}

	return {
		init: function(){
			$('form#search-line').on('submit', function(e){e.preventDefault();});
			var search_box = $('#search-line input');
			search_box.on('input', search);
			var result = $('#search-line #results');
			search_box.on('focus', function(e){result.css('display','block')});
			$(document).on('click', function(e){
				var target = $(e.target);
				if(!target.closest('form#search-line').length){
					result.css('display', 'none');
				}
			});
		}
	};
})();
