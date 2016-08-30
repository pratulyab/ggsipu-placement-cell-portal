var Search = (function() {
	'use strict';

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
		var ul = $('#search #results');
		if (!ul){
			ul = $('<ul id="results"/>');
			$('form#search').append(ul);
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
		$('#search #results').empty();
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
			$('form#search').on('submit', function(e){e.preventDefault();});
			var search_box = $('#search input');
			search_box.on('input', search);
			var result = $('#search #results');
			search_box.on('focus', function(e){result.css('display','block')});
			$(document).on('click', function(e){
				var target = $(e.target);
				if(!target.closest('form#search').length){
					result.css('display', 'none');
				}
			});
		}
	};
})();
