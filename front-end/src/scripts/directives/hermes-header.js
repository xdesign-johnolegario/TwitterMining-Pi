angular.module('UxDesigns')

.directive('hermesHeader', ["$rootScope", function ($rootScope) {
    return {
        restrict: 'E',
        replace: true,
        templateUrl: "components/hermes-header.html",
        link: function($scope, elm, attr){

        		


				$scope.addTwitter = function() {
				 	$rootScope.$broadcast("search", $scope.twitterSearch);
				}

				$scope.mostRetweeted = function() {
					$rootScope.$broadcast("mostRetweets", "mostRetweetResults");

				};

				$scope.mostLiked = function() {
					console.log("din still smells");
					$rootScope.$broadcast("mostLikes", "mostLikesResults");


				}


				/*addTwitter()
				broadcst event rootscope

				$rootScope.$broadcast("searchPerformed", $scope.)


				$scope.$on("search", function($event, arg){
					$scope.newVar = arg.searchobject
				})

        		*/


        }
    };
}]);