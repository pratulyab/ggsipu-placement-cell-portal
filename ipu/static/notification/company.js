var Notification = (function() {
	'use strict'
    var indices = [];
    function handleMultipleJquery(){
        $('a').unbind('click'); // to prevent multiple fires because of reloading of jquery in the rendered template.
        document.getElementById('create-notifications').removeEventListener('click', generateNewForm);
        $('#dropdown3').on('click', function(e){e.stopPropagation();});
        $('.dropdown-button').on('click', function(e){e.preventDefault()});
        $('nav .brand-logo').on('click', function(e){location.href='';});
        document.getElementById('create-notifications').addEventListener('click', generateNewForm);
         // Handles the left panel notification button.
        $('#notification-anchor').on('click' , function(e){$('#your-notifications').trigger('click');});//Handles the maine notification tab button.
        $('#dropdown1 a').each(function(i, a){
            var el = $(a);
            var target = el.data('links');
            if (!target)
                return true;
            var target_el = $('#tab-bar').find("[href='#" + target + "']");
            if(!target_el.length)
                return true;
            el.on('click', function(e){e.preventDefault();target_el[0].click();});
        });
    }

//Notification Starts.
//Follow the flow. Up to Down.
//Gets the first form. Asks to select the streams.
//==============================================================================//
//============Below are functions to get a faculty's notifications.=============//
    function getNotifications() {
        var url = $('#notification-anchor').attr('url');
        $.ajax({
            url : url,
            type : 'GET',
            async : true,
            beforeSend: function() {
                showPreloader();
            },
            complete: function() {
                removePreloader();  
            },
            success : function(data, status, xhr){
                populateDiv(data);                
            }
        });       
    }

    function populateDiv(data) {
        var raw_html = '';  
        var icon = '';
        if(data.length === 0){
            icon = '<i class="material-icons circle">report_problem</i>' 
            raw_html = '<li class="collection-item avatar">' + icon + '<span class="title">' + 'None' + '</span>' + '<p>' + 'No notifications found.' + '</p>' + '</li>';
            $('#your-notifications-div-ul').html(raw_html);
            return;
        }                   
        for(var i = 0 ; i < data.length ; i++){
            icon = ( (data[i].read === true) ? '<i class="material-icons circle blue">done_all</i>' : '<i class="material-icons circle red">fiber_new</i>');
            raw_html += '<li class="collection-item avatar">' + icon + 
                '<span class="title">' + data[i].actor + '</span>' + '<p>' + data[i].message + '</p>' + '</li>';
        }
        $('#your-notifications-div-ul').html(raw_html);
        Download.serve();

    }

    
    function viewNotifications(e) {
        e.preventDefault();
        getNotifications();
    }

//==============================End============================//

	return {
		init: function() {
            document.getElementById('notification').addEventListener('click' , viewNotifications);
			// mobile
            document.getElementById('m-notification').addEventListener('click' , viewNotifications);
		}
	}

})();


