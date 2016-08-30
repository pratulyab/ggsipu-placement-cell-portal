var GetNotification = (function()  {

	function populateNotifications(data) {
		raw_html = '';

		for(var i = 0; i < data.length; i++){
			raw_html += '<div id="noti-head">Notifications' +'</div>' + '<li>' +
            '<div class="collapsible-header">From : ' + data[i].actor + '</div>' +
            '<div class="collapsible-body"><p>' + data[i].message + '</p></div>' + 
          	'</li>'
		}
		$('#dropdown3').html(raw_html);
	}


	function getNotifications(e) {
        e.preventDefault();
        var url = $('#notification_button').attr('href');
        $.ajax({
            url : url,
            type : 'GET',
            async : true,
            success : function(data, status, xhr){
                populateNotifications(data);
            }
        });
        
    }

	return {
		init : function() {
			$('#notification_button').on('click' , getNotifications)
		}
	}
})();