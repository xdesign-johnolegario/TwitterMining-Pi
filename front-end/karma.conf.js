// Karma configuration
// Generated on Wed Nov 26 2014 15:36:16 GMT+0000 (GMT Standard Time)

module.exports = function(config) {
  config.set({

    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: __dirname,


    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['jasmine', 'chai', 'sinon', 'chai-sinon'],


    // list of files / patterns to load in the browser
    files: [
        // angular js must come before angular-mocks
      'bower_components/jquery/dist/jquery.js',
      'target/scripts/angular.js',
      'target/scripts/angular-aria.js',
      'bower_components/angular-mocks/angular-mocks.js',
      'target/css/**/*.css',
      'target/scripts/**/*.js',
      './.tmp/templates.js',
      'tests/**/*.js',
      'tests/img/image.jpg',
      'tests/fonts/font.tff'
    ],

    proxies: {
      '/img/image.jpg': '/base/tests/img/image.jpg',
      '/base/target/fonts/MarselisWeb.woff': '/base/tests/img/image.jpg',
      '/base/target/fonts/font-awesome/fontawesome-webfont-ttf.ttf?v=4.5.0': '/base/tests/fonts/font.tff',
      '/base/target/fonts/font-awesome/fontawesome-webfont-woff.woff?v=4.5.0': '/base/tests/fonts/font.tff',
      '/base/fonts/font-awesome/fontawesome-webfont-ttf.ttf?v=4.5.0': '/base/tests/fonts/font.tff'
    },

    // list of files to exclude
    exclude: [
      //'**/*.min.js'
    ],

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://npmjs.org/browse/keyword/karma-reporter
    reporters: ['progress'],


    // web server port
    port: 9876,


    // enable / disable colors in the output (reporters and logs)
    colors: true,


    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,


    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,


    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['PhantomJS'],


    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false
  });
};
