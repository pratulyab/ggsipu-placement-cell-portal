var Utils = (function() {
	$info_modal = $('#info-modal');

	function reloadContent() {
		$active = is_mobile_view ? $('#sideNav-tabs li.active').not('.expandable') : $('#main-tabs > li > .active');
//		$content_div = is_mobile_view ? ($active.hasClass('child-li') ? $active.data('child_div') : $active.data('main_div')) : $active.attr('href');
		if (!is_mobile_view)
			$active = $active.parent(); // because events are set on li
		$active.trigger('reload'); //account for reload event
	}

	function displayInfoModal() {
		// if mobile view, then $active is an <li>, otherwise if not, then it is <a> tag
		$active = is_mobile_view ? $('#sideNav-tabs li.active').not('.expandable') : $('#main-tabs > li > .active');
		$content_div = is_mobile_view ? ($active.hasClass('child-li') ? $active.data('child_div') : $active.data('main_div')) : $active.attr('href');
		$content_div = $($content_div);
		var $pinfo = $content_div.find('p.info'),
			heading, 
			info = $pinfo.length ? $pinfo.text() : 'No information to display';
		if (is_mobile_view) {
			heading = $active.children('a').first().text().trim();
		} else {
			heading = $active.text().trim();
			$vertical_tabs = $content_div.find('.vertical-tabs');
			if ($vertical_tabs.length) {
				// then heading should be one of the vertical tab
				heading = $vertical_tabs.find('li > a.active').text().trim();
			}
		}
		$info_modal.find('.modal-content > .heading').text(heading);
		$info_modal.find('.modal-content > p').text(info);
		$info_modal.modal('open');
	}
	
	return {
		'init': function(params){
			// Fixed Action Button
			if (params.fab) {
				var $reload_btn = $('.reload-btn'),
					$info_btn = $('.info-btn');
				// Tooltips + Click Event
				$reload_btn.tooltip({delay: 50, 'tooltip': 'Reload', 'position': 'left'});
				$reload_btn.on('click', reloadContent);
				$info_btn.tooltip({delay: 50, 'tooltip': 'Information', 'position': 'left'});
				$info_btn.on('click', displayInfoModal);
			}
		}
	}
})();
