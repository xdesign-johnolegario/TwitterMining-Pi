angular.module('UxDesigns', ['ngRoute', 'matchMedia', 'ngSanitize'])

    .config(['$routeProvider', '$locationProvider', function ($routeProvider, $locationProvider) {
        $routeProvider.
        when('/', {
            templateUrl: 'pages/landing-page.html',
            controller: 'LandingPageController'            
        }).
        otherwise({
            redirectTo: '/'
        });

        $locationProvider.html5Mode(true);
    }])