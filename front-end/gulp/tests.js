module.exports = (function() {
    'use strict';

    var gulp = require('gulp'),
        jshint = require('gulp-jshint'),
        karma = require('karma').server,
        config = require('./config.js');

    gulp.task('check', function() {
        return gulp.src(config.mainSrc)
            .pipe(jshint())
            .pipe(jshint.reporter('default'))
    });

    function startKarma(single, cb) {
        karma.start({
            configFile: __dirname + '/../karma.conf.js',
            singleRun: single
        }, function() {cb;});
    }

    gulp.task('test', ['check', 'templatecache'], function (done) {
        startKarma(true, done);
    });

    gulp.task('test-watch', function (done) {
        startKarma(false, done)
    });

    gulp.task('build-and-test', ['build', 'check', 'templatecache'], function (done) {
        startKarma(true, done);
    });

    return {
        startKarma: startKarma
    }
})();