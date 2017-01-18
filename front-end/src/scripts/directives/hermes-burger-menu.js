angular.module('UxDesigns')

.directive('hermesBurgerMenu', function () {
    return {
        restrict: 'E',
        replace: true,
        scope: {
            menuItems: '=',
            toggleMenu: '&',
            showMenu: '=',
            maxScreenSize: '@'
        },
        templateUrl: "components/hermes-burger-menu.html",
        link: function (scope, element, attrs) {
            switch (scope.maxScreenSize) {
                case 'x-small': element.addClass('col-sm-hidden'); break;
                case 'medium': element.addClass('col-lg-hidden'); break;
                case 'small': element.addClass('col-md-hidden'); break;
                default: element.addClass('col-md-hidden'); break;
            }
        }
    };
});