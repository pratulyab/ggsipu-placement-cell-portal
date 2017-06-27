//=========================Preloader Functions Begins====================//
	var preloader = document.getElementById('page-preloader');
	var preloader_shadow = document.getElementById('preloader-shadow');

	function showPreloader(){
		var h = window.innerHeight;
 		var w = window.innerWidth;
 		addPreloaderShadow(h , w);
 		preloader.style.top = h/3 + 'px';
 		preloader.style.left = w/2 + 'px';
 		preloader.style.display = 'block';
	}

	function addPreloaderShadow(h , w){
		preloader_shadow.style.height = h + 'px';
  		preloader_shadow.style.width = w + 'px';
  		preloader_shadow.style.display = 'block';
	}

	function removePreloader(){
		preloader.style.display = 'none';
		preloader_shadow.style.display = 'none';
	}
	
	function getReportForm(){
		var url = $('#report-form-anchor').attr('href');
		$.ajax({
			url : url,
			type : 'GET',
			beforeSend: function() {
   				showPreloader();
            },
            complete: function() {
            	$('select').material_select(); 
            	grecaptcha.render('report-form-recaptcha-div', {'sitekey': '6Lf15yUUAAAAAI1ju9iGXNQQQFKhIQU41J5ccaDC'});	
            	var delayRemover = 2000; 
				setTimeout(function() {
					removePreloader();
				}, delayRemover);
            },
            success : function(data , status , xhr){
				document.getElementById('report-form-content').innerHTML = data;
				document.getElementById('close-report-form').addEventListener('click' , function(e) {e.preventDefault(); $('#report-form-modal').modal('close');});
				//document.getElementById('submit-report-form').addEventListener('click' , submitReportForm);
				
			}	
		})
	}
//=============================Preloader Function Ends===================//

var Utils = (function() {
	$info_modal = $('#info-modal');

	function reloadContent() {
		$active = is_mobile_view ? $('#sideNav-tabs li.active').not('.expandable') : $('#main-tabs > li > .active');
//		$content_div = is_mobile_view ? ($active.hasClass('child-li') ? $active.data('child_div') : $active.data('main_div')) : $active.attr('href');
		if (!is_mobile_view)
			$active = $active.parent(); // because events are set on li
		$active.trigger('reload'); //account for reload event
		var $span = $('<span class="green-text text-lighten-1" />').html("Tab Reloaded!").css('fontWeight', 'bold');
		Materialize.toast($span, 2000);
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
	
	function initializeReportBugModal(e){
		e.preventDefault();
		document.getElementById('report-form-modal-trigger').click();
		showPreloader();
	}

	function submitReportForm(e){
		e.preventDefault();
		var url = $('#submit-report-form').attr('href');
		console.log(url);
	}

	return {
		init: function(params){
			// Fixed Action Button
			if (params.fab) {
				var $reload_btn = $('.reload-btn'),
					$info_btn = $('.info-btn');
				// Tooltips + Click Event
				$reload_btn.tooltip({'delay': 50, 'tooltip': 'Reload Tab', 'position': 'left'});
				$reload_btn.on('click', reloadContent);
				$info_btn.tooltip({'delay': 50, 'tooltip': 'Tab Information', 'position': 'left'});
				$info_btn.on('click', displayInfoModal);
				document.getElementById('report-form-anchor').addEventListener('click' , initializeReportBugModal);
				$('#fixed-action-button').find('a')[0].click();
			}
		}
	}
})();
