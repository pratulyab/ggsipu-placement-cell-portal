var Mobile = (function () {
	var $tabContentDivs,
		$tabBarLIs,
		$current;

	function handleDisplay(e) {
		e.preventDefault();
		console.log($(this));
	}

	return {
		init: function () {
			if (! /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent ))
				return;
			
			$tabContentDivs = $('#tabs-data-div > div');
			$tabBarLIs = $('#main-tabs > li');
			$tabBarLIs.on('click', handleDisplay);
		}
	}
})();
