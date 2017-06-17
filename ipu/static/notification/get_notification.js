var GetNotification = (function()  {

	function populateNotifications(data) {
		raw_html = '<div id="noti-head">Notifications' +'</div>';
		for(var i = 0; i < ( (data.length < 5) ? data.length : 5 ) ; i++){
			raw_html += '<li>' +
            '<div class="collapsible-header">From :' + data[i].actor + '</div>' +
            '<div class="collapsible-body"><p>' + data[i].subject + '</p></div>' + 
          	'</li>'
		}
        if (data.length==0) {
            raw_html += '<div id="noti-content">You have no notifications currently</div>';
        }


        if (data.length>0) {
            raw_html += '<div id="noti-foot"><a id="noti-foot-anchor" href="#notifications">See Older Notifications' + '</a></div>';    
        }
        

        
		$('#dropdown3').html(raw_html);
        $('#noti-foot-anchor').on('click' , function () {
            $('#notification_button').trigger('click');
        });
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
                $('#notifications_badge').remove();
            }
        });
        
    }

	return {
		init : function() {
			document.getElementById('notification_button').addEventListener('click' , getNotifications)
		}
	}
})();