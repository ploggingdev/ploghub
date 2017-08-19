function handle_post_vote(id, type){
    
        if((type != 'up' && type != 'down') || !Number.isInteger(id)){
            alert("Oops, an error was encountered.");
            return;
        }
    
        var csrftoken = getCookie('csrftoken');
    
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                    xhr.setRequestHeader("X-CSRFToken", csrftoken);
                }
            }
        });
    
        if(type == "up"){
            vote_value = 1;
        }
        else if(type == "down"){
            vote_value = -1;
        }
        upvote_selector = "#"+id+"-post-up"
        upvote_item = $( upvote_selector );
        downvote_selector = "#"+id+"-post-down"
        downvote_item = $( downvote_selector );
        points_selector = "#"+id+"-post-points"
        points_item = $( points_selector );
    
        $.ajax({
        
           // The URL for the request
           url: "/votepost/"+id+"/",
        
           // The data to send (will be converted to a query string)
           data: {
               vote_value: vote_value
           },
        
           // Whether this is a POST or GET request
           type: "POST",
        
           // The type of data we expect back
           dataType : "json",
       })
         // Code to run if the request succeeds (is done);
         // The response is passed to the function
         .done(function( json ) {
            var vote_diff = json.vote_diff;
            if (vote_value == -1) {
                if (upvote_item.attr("style") != undefined) { // remove upvote, if any.
                    upvote_item.removeAttr("style")
                }
                if (downvote_item.attr("style") != undefined) { // Canceled downvote
                    downvote_item.removeAttr("style")
                } else {                                // new downvote
                    downvote_item.attr("style", "color : orangered")
                }
            } else if (vote_value == 1) {               // remove downvote
                if (downvote_item.attr("style") != undefined) {
                    downvote_item.removeAttr("style")
                }
    
                if (upvote_item.attr("style") != undefined) { // remove upvote, if any.
                    upvote_item.removeAttr("style");
                }else {                                // adding new upvote
                    upvote_item.attr("style", "color : orangered");
                }
            }
    
            // update score element
            points = parseInt(points_item.text());
            points_item.text(points += vote_diff);
         })
         // Code to run if the request fails; the raw request and
         // status codes are passed to the function
         .fail(function( xhr, status, errorThrown ) {
           alert( "Sorry, there was a problem registering your vote. Please login, if have not done so." );
         });
    }
    
    // using jQuery
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    
    function get_points_suffix(val){
        if(val == 1 || val == -1){
            return "point";   
        }
        else{
            return "points";
        }
    }