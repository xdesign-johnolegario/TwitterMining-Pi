$(document).ready(function(){
    // Prevent page being cached on back button press
    $(window).bind("pageshow", function(event) {
        if (event.originalEvent.persisted) {
            window.location.reload();
        }
    });
});

function scrollToTopOfPage() {
	$('html, body').animate({
        scrollTop: 0
    }, 500);
}
