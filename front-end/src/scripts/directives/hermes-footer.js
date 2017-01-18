angular.module('UxDesigns')

.directive('hermesFooter', function () {
    return {
        restrict: 'E',
        replace: true,
        templateUrl: "components/hermes-footer.html"
    };
});