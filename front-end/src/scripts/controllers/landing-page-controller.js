angular.module('UxDesigns')

.controller('LandingPageController', ['$scope', '$location', '$http', '$interval', '$route', '$window', function($scope, $location, $http, $interval, $route, $window) {


	getTweets();

	function getTweets() {
		$http.get('http://localhost:8000/htweets2/?format=json')
    	.then(function(res) {
			
			
			$scope.twitterResult = 0;

    		$scope.twitterResult = res.data;			

			$scope.twitterResult.ready = true;

			$scope.slickConfig = {
				enabled: true,
				autoplay: true,
            	draggable: true,
            	fade: true,
            	speed: 1500,
            	autoPlaySpeed: 2000,
				pauseOnHover: false,
            	dots: false,
            	lazyLoad: "ondemand",
            	arrows: true,
            	mobileFirst: true,
            	method: {},
            	event: {
            	    beforeChange: function (event, slick, currentSlide, nextSlide) {
            	    },
            	    afterChange: function (event, slick, currentSlide, nextSlide) {
            	    }
            	}
			}

			$scope.twitterResult.ready = true;
    	});
	}

    $scope.getColor = function(status, score) {
        if(status == 'normal'){
            return 'color: blue'
        } else {
            if(status == 'neutral' || score == 'alert') {
                return 'color: yellow'
            } else {
                return 'color: red'
            }
        }
    }

	$interval(function() {
		
		$scope.slickConfig.enabled = !$scope.slickConfig.enabled;
		$scope.twitterResult.ready

		getTweets();
	}, 60000);

	

    	$scope.slickConfig = {
    		enabled: true,
            autoplay: true,
            draggable: true,
            fade: true,
            speed: 1500,
            autoPlaySpeed: 2000,
            pauseOnHover: false,
            dots: false,
            lazyLoad: "ondemand",
            arrows: true,
            mobileFirst: true,
            method: {},
            event: {
                beforeChange: function (event, slick, currentSlide, nextSlide) {
                },
                afterChange: function (event, slick, currentSlide, nextSlide) {
                }
            }
        };


}]);
