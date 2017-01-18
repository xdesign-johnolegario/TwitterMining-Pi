angular.module('UxDesigns')

.controller('LandingPageController', ['$scope', '$location', function($scope, $location) {

	

	$scope.searchResult = [
		{
			search: "myHermes",
			content: [
			{
				username: "@Dom",
				tweet: "Hermes are awesome!",
				dateTweeted: "19th May 1994",
				location: "Liverpool",
				retweets: 47,
				likes: 78
			}
			]
		}

	];

	$scope.$on("search", function($event, arg){
		addTwitter(arg);
	});

	$scope.$on("mostRetweets", function($event, arg){			
		mostRetweeted(arg);
	});

	$scope.$on("mostLikes", function($event, arg){
		mostLiked(arg);
	});



	function addTwitter(searchTerm) {

		console.log(searchTerm);

		//DO TWITTER BACK END STUFF HERE

		$scope.twitterReturn = {
			search: searchTerm,
			content: [
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				}

			]
			
		};

		$scope.searchResult.push($scope.twitterReturn);

		//console.log($scope.searchResult);
		

	};

	function mostRetweeted(retweet) {
		console.log(retweet);

		$scope.twitterReturn = {
			search: retweet,
			content: [
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},
				{ 
					username: "@Dave", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "25th June 1966", 
					location: "Liverpool",
					retweets: 45,
					likes: 62
				},

			]
			
		};

		$scope.searchResult.push($scope.twitterReturn);



	}; 

	function mostLiked(like) {
		console.log(like);

		$scope.twitterReturn = {
			search: like,
			content: [
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				},
				{ 
					username: "@Dawn", 
					tweet: "I'm trying not to, kid. Hey, Luke! May the Force be with you. But with the blast shield down, I can't even see! How am I supposed to fight? Your eyes can deceive you.", 
					dateTweeted: "24th July 1962", 
					location: "Liverpool",
					retweets: 7,
					likes: 12
				}

			]
			
		};

		$scope.searchResult.push($scope.twitterReturn);
	}	


}]);