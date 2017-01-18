(function() {
'use strict'

angular.module('UxDesigns')

    .controller('MainController', ['$scope', 'screenSize', function($scope, screenSize) {
        /**
         * Broadcast listeners
         */
        $scope.$on('$routeChangeSuccess', function () {
            scrollToTopOfPage();
        });
        $scope.$on('loading', function () {
            loading();
        });
        $scope.$on('done-loading', function () {
            hideLoading();
        });

        activate();

        function activate() {
            $scope.showmenu = true;

            if (screenSize.is('xs') || screenSize.is('sm')) {
                $scope.showmenu = false;

                $scope.toggleMenu = function () {
                    $scope.showmenu = ($scope.showmenu) ? false : true;
                };
            }

            //Check window size on resize
            $scope.isMobile = screenSize.on(['xs', 'sm'], function () {
                $scope.showmenu = false;

                $scope.toggleMenu = function () {
                    $scope.showmenu = ($scope.showmenu) ? false : true;
                };
            });
        }

        function hideNavigation() {
            $rootScope.showmenu = false;
        }

        function showNavigation() {
            $rootScope.showmenu = true;
        }

        $scope.headerRHS = "<div ng-include src=\"'components/header-rhs.html'\"></div>";
    }]);

})();