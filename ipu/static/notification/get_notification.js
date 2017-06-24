var GetNotification = (function()  {

	function populateNotifications(data) {
		var raw_html = '<h3 id="side-nav-head">Notifications</h3>';
        for(var i = 0; i < ( (data.length < 5) ? data.length : 5 ) ; i++){
			raw_html += '<li><div class="divider"></div></li>' + '<li><div id="noti-div"><div id="noti-heading"><h3 class="truncate">' 
                        + data[i].sender + '</h3><h4>'
                         + data[i].date + '</h4></div><div id="noti-content"><h5>'
                         + data[i].message + '</h5></div></div></li>';
		}
        if (data.length==0) {
            raw_html = '<li><div class="divider"></div></li><li id="noti-element"><div><div><h5>No Messages</h5></div></div></li><li><div class="divider"></div></li>';
            return;
        }        
        raw_html += '<li><div class="divider"></div></li><li><a href="" id="noti-button" style="color : coral !important;">See All Notifications</a></li><li><div class="divider" style="margin-top : 0"></div></li>'
		document.getElementById('slide-out2').innerHTML = raw_html;
        document.getElementById('noti-button').addEventListener('click' , function (e) {
            e.preventDefault();
            document.getElementById('notification').click();
        });
	}


	function obtainPings(e) {
        e.preventDefault();
        var url = $('#notification_button').attr('url');
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
			document.getElementById('notification_button').addEventListener('click' , obtainPings)
		}
	}
})();