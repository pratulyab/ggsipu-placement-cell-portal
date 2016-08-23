$("#notification").click(function () {
        	var options;
            $.get( "{% url 'generate_notifications' %}" , {}, function( data ) {
            	console.log(data);
            	$("#tab3").html(data); 
            });
        });