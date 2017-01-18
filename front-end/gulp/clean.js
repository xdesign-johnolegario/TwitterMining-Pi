(function() {
'use strict';

    var gulp = require('gulp'),
        del = require('del'),
        config = require('./config.js');

    gulp.task('clean', ['clean:dev','clean:build'], function () {
        // No op
    });

    gulp.task('clean:dev', function (done) {
        del(config.devLib, done);
    });

    gulp.task('clean:build', function (done) {
        del([config.devLib, config.destination], done);
    });
})();