var HomePage = (function() {
    
    var settings_list_display = "flexnone";
    var mob_left_panel_display = "flexnone";
    
    //Search
    function search(){
    }
    
    function displaySearch(e){
        if (window.innerWidth <= 992){
            var el = document.getElementById("search-full");
            if(document.defaultView.getComputedStyle(el).display == "block")
                el.style.display = "none";
            else
                el.style.display = "block";
            return;
        }
        var fa = e.target || e.srcElement;
        var el = document.getElementsByClassName('search')[0];
        try{
            var display = document.defaultView.getComputedStyle(el).visibility;
        }
        catch(e){
            return;
        }
        
        if (display == "hidden"){
            el.style.visibility = "visible";
            document.querySelector('.search input').focus();
        }
        else{
            search();
        }
    }
    
    function hideSearch(e){
        var input = e.target || e.srcElement;
        document.querySelector('.search input').value = "";
        input.parentElement.style.visibility = "hidden";
    }
    
    //Settings
    function handleSettingsDisplay(e){
        document.getElementById('settings-list').style.display = settings_list_display.substr(0,4);
        settings_list_display = settings_list_display.substr(4,9) + settings_list_display.substr(0,4);
    }
    
    //Tab Selector
    function moveTabSelector(e) {
        var li = e.target.parentElement;
        var posn = (li.offsetLeft / li.parentElement.offsetWidth) * 100;
        if (posn < 50){
            document.getElementById('current-tab-selector').style.alignSelf = "flex-start";
        }
        else{
            document.getElementById('current-tab-selector').style.alignSelf = "flex-end";
        }
    }
    
    // Hamburger Menu
    function mobileLeftPanel(e){
        var el = document.getElementsByClassName('left-panel')[0];
        el.style.display = mob_left_panel_display.substr(0,4);
        if (mob_left_panel_display[0] == 'f'){
            el.style.position = "relative";
            document.querySelectorAll('.tabs .tab label')[0].style.fontSize = "10px";
            document.querySelectorAll('.tabs .tab label')[1].style.fontSize = "10px";
        }
        else{
            el.style.position = "absolute";
            document.querySelectorAll('.tabs .tab label')[0].style.fontSize = "20px";
            document.querySelectorAll('.tabs .tab label')[1].style.fontSize = "20px";
        }
        mob_left_panel_display = mob_left_panel_display.substr(4,9) + mob_left_panel_display.substr(0,4);
    }
    
    return {
        init: function() {
            // Search
            document.querySelector('.nav-links .fa-search').addEventListener('click', displaySearch);
            document.getElementById('search-close').addEventListener('click', hideSearch);
            document.querySelector('.search input').addEventListener('keydown', function(e){
                if(e.keyCode == 13){
                    search();
                }
            })
            
            // Settings
            document.getElementById('settings').addEventListener('click', handleSettingsDisplay);
            document.getElementById('settings-list').addEventListener('mouseleave', handleSettingsDisplay)
            
            //    Movement of tab selector
            var li = document.getElementsByClassName('tab');
            for (var i = 0; i < li.length; i++)
                li[i].getElementsByTagName('label')[0].addEventListener('click', moveTabSelector);
            
            // Hamburger Menu
            document.querySelector('.mobile-toggle').addEventListener('click', mobileLeftPanel)
            
            // Search Full Close
            document.querySelector('#search-full .fa-close').addEventListener('click', function(e){
                document.getElementById('search-full').style.display = "none";
            })
        }
    };
}());
