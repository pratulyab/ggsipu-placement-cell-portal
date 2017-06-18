is_mobile_view = false; // Global

var Mobile = (function () {
	var $tabContentDivs,
		$sideBarLis,
		$currentParentLi,
		$currentChildLi,
		PARENT_LI_COLOR_CLASS = 'blue lighten-5 active',
		CHILD_LI_COLOR_CLASS = 'teal lighten-5 active';

	function handleDisplay(e) {
		var $li = $(this),
			$content_div = $($li.data('main_div') ? $li.data('main_div') : $li.parents('li.expandable').data('main_div'));

		// Toggle Main Tab Display
		$tabContentDivs.not($content_div).hide();
		$content_div.show();
		
		// Colour Management
		$currentParentLi.removeClass(PARENT_LI_COLOR_CLASS);
		
		if ($currentChildLi)
			$currentChildLi.removeClass(CHILD_LI_COLOR_CLASS);
		
		if ($li.hasClass('child-li')){
			// Toggle V-Tab Display
			var sibling_divs = [];
			$li.siblings().each(function(i, el){
				sibling_divs.push($(el).data('child_div'));
			});
			$(sibling_divs).each(function(i, el){
				$(el).hide();
			});
			$($li.data('child_div')).show();
			// Colour Management
			$currentParentLi = $li.parents('li.expandable');
			$currentChildLi = $li;
			$li.addClass(CHILD_LI_COLOR_CLASS);
		} else {
			$currentParentLi = $li;
			$currentParentLi.addClass(PARENT_LI_COLOR_CLASS);
		}
	}

	return {
		init: function () {
			if (! /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent))
//			if (!(window.innerWidth <= 800 && window.innerHeight <= 600))
				return;
			is_mobile_view = true;
			$tabContentDivs = $('#tabs-data-div > div');
			$sideBarLis = $('#sideNav-tabs li').not('.no-padding').not('.expandable');
			$sideBarLis.on('click', handleDisplay);
			$currentParentLi = $sideBarLis.first();
			$currentParentLi.addClass(PARENT_LI_COLOR_CLASS);
			
			// Handling Vertical Tabs Display
			var $vertical_tabs = $('.vertical-tabs'),
				$vtabs_div = $vertical_tabs.find('.tabs').parent(),
				$vtabs_content_div = $vtabs_div.next();
			$vtabs_div.remove(); // Removing the vertical tabs
			$vtabs_content_div.attr('class', 'col s12'); // Changing the vertical tabs' content div to occupy full screen
			$vertical_tabs.removeClass('vertical-tabs'); // To be on the safer side
		}
	}
})();
