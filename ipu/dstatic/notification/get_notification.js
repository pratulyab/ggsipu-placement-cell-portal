var GetNotification = (function()  {

	function populateNotifications(data) {
		raw_html = '<div id="noti-head">Notifications' +'</div>';
		for(var i = 0; i < ( (data.length < 5) ? data.length : 5 ) ; i++){
			raw_html += '<li>' +
            '<div class="collapsible-header">From :' + data[i].actor + '</div>' +
            '<div class="collapsible-body"><p>' + data[i].message + '</p></div>' + 
          	'</li>'
		}
        console.log("yeah2");

        raw_html += '<div id="noti-foot"><a id="noti-foot-anchor" href="#notifications">See Older Notifications' + '</a></div>';

        
		$('#dropdown3').html(raw_html);
        $('#noti-foot-anchor').on('click' , function () {
            $('#notification_button').trigger('click');
            console.log("yeah");
        });
	}


	function getNotifications(e) {
        console.log("yeah3");
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