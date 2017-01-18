$(document).ready(function(){
    window.showSpinner = true;

	window.loading = function(){
        if(window.showSpinner) {

            var screenWidth = $('window').innerWidth();
            var screenHeight = $('window').innerHeight();
            $("#loadingBackground").css('height', screenHeight + 'px');
            $("#loadingBackground").css('width', screenWidth + 'px');



            $("#loadingBackground").css('top', '0px');
            $("#loadingBackground").css('left', '0px');

            $("#loadingBackground").show();
            $("#loading").show();
            $("body").addClass('loading');
        }
	};

    window.hideLoading = function(){
        $("#loadingBackground").hide();
        $("#loading").hide();
        $("body").removeClass('loading');
    };

    hideLoading();
});
