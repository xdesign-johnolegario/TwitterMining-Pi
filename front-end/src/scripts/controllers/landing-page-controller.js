angular.module('UxDesigns')

.controller('LandingPageController', ['$scope', '$location', '$http', '$timeout', '$interval', function($scope, $location, $http, $timeout, $interval) {


	getTweets();

	function getTweets() {
		$http.get('http://localhost:8000/htweets/?format=json')
    	.then(function(res) {

			$scope.twitterResult = 0;

    		//load here

    		$scope.twitterResult = res.data;

    		// $timeout(function() {
		    	
		    // }, 100);
			$scope.twitterResult.ready = true;
		    //end load here
    		console.log(res);
			
    	});
		console.log("please repeat");
	}

	

	$interval(function() {
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
            // dotsClass: "slick__dots",
            arrows: true,
            // prevArrow: '<div class="slick__Prev-Arrow"><span class="fa fa-angle-left"></span><span class="sr-only">Prev</span></div>',
            // nextArrow: '<div class="slick__Next-Arrow"><span class="fa fa-angle-right"></span><span class="sr-only">Next</span></div>',
            mobileFirst: true,
            method: {},
            event: {
                beforeChange: function (event, slick, currentSlide, nextSlide) {
                },
                afterChange: function (event, slick, currentSlide, nextSlide) {
                }
            }
        };



	// $scope.searchResult = [
	// 	{
	// 		search: "",
	// 		content: [
	// 		{
	// 			username: "",
	// 			tweet: "",
	// 			dateTweeted: "",
	// 			location: "",
	// 			retweets: ,
	// 			likes: 78
	// 		}
	// 		]
	// 	}

	// ];

	// $scope.$on("search", function($event, arg){
	// 	addTwitter(arg);
	// });

	// $scope.$on("mostRetweets", function($event, arg){			
	// 	mostRetweeted(arg);
	// });

	// $scope.$on("mostLikes", function($event, arg){
	// 	mostLiked(arg);
	// });


	// function addTwitter(searchTerm) {

	// 	console.log(searchTerm);

	// 	//DO TWITTER BACK END STUFF HERE

	// 	$scope.twitterReturn = {
	// 		search: searchTerm,
	// 		content: [
	// 			{ 
	// 				username: "@Dave", 
	// 				tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
	// 				dateTweeted: "25th June 1966", 
	// 				location: "Liverpool",
	// 				retweets: 45,
	// 				likes: 62
	// 			}

	// 		]
			
	// 	};

	// 	$scope.searchResult.push($scope.twitterReturn);

	// 	//console.log($scope.searchResult);
		

	// };

	// function mostRetweeted(retweet) {
	// 	console.log(retweet);

	// 	$scope.twitterReturn = {
	// 		search: retweet,
	// 		content: [
	// 			{ 
	// 				username: "@Dave", 
	// 				tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
	// 				dateTweeted: "25th June 1966", 
	// 				location: "Liverpool",
	// 				retweets: 45,
	// 				likes: 62
	// 			}

	// 		]
			
	// 	};

	// 	$scope.searchResult.push($scope.twitterReturn);

	// }; 

	// function mostLiked(like) {
	// 	console.log(like);

	// 	$scope.twitterReturn = {
	// 		search: like,
	// 		content: [
	// 			{ 
	// 				username: "@Dawn", 
	// 				tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
	// 				dateTweeted: "24th July 1962", 
	// 				location: "Liverpool",
	// 				retweets: 7,
	// 				likes: 12
	// 			}
	// 		]			
	// 	};

	// 	$scope.searchResult.push($scope.twitterReturn);
	// }	


}]);