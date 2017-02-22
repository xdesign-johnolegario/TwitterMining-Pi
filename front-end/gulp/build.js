(function() {
    'use strict';

    var gulp = require('gulp'),
        gutil = require('gulp-util'),
        config = require('./config.js'),
        concat = require('gulp-concat'),
        sourcemaps = require('gulp-sourcemaps'),
        uglify = require('gulp-uglify'),
        bower = require('gulp-bower'),
        bowerFiles = require('main-bower-files'),
        merge = require('merge-stream'),
        minifyCSS = require('gulp-minify-css'),
        path = require('path'),
        sass = require('gulp-sass'),
        replace = require('gulp-replace'),
        debug = require('gulp-debug'),
        useref = require('gulp-useref'),
        del = require('del'),
        webserver = require('gulp-webserver');
    var args = require('yargs').argv;
    var $ = require('gulp-load-plugins')({lazy: true});

    /**
     * Formatter for bytediff to display the size changes after processing
     * @param  {Object} data - byte data
     * @return {String}      Difference in bytes, formatted
     */
    function bytediffFormatter(data) {
        var difference = (data.savings > 0) ? ' smaller.' : ' larger.';
        return data.fileName + ' went from ' +
            (data.startSize / 1000).toFixed(2) + ' kB to ' +
            (data.endSize / 1000).toFixed(2) + ' kB and is ' +
            formatPercent(1 - data.percent, 2) + '%' + difference;
    }

    /**
    * Minifiy JavaScript
    */
    gulp.task('minjs', function () {
        return gulp.src('bower_components/angular-media-queries/**/*.js')
            .pipe(useref())
            .pipe(uglify())
            .pipe(concat('match-media.min.js'))
            .pipe(gulp.dest('./target/scripts'));
    });

    /**
     * Compile sass to css
     * Fixes glyphicon filenames. They need a "-eof".eof to work with magnolia
     * @return {Stream}
     */
    gulp.task('styles', function() {
        // Compile the sass
        gulp.src(config.sassSrc)
            .pipe(sass().on('error', sass.logError))
            .pipe(debug())
            .pipe(replace('glyphicons-halflings-regular.eot', 'glyphicons-halflings-regular-eot.eot'))
            .pipe(replace('glyphicons-halflings-regular.woff2', 'glyphicons-halflings-regular-woff2.woff2'))
            .pipe(replace('glyphicons-halflings-regular.woff', 'glyphicons-halflings-regular-woff.woff'))
            .pipe(replace('glyphicons-halflings-regular.ttf', 'glyphicons-halflings-regular-ttf.ttf'))
            .pipe(replace('glyphicons-halflings-regular.svg', 'glyphicons-halflings-regular-svg.svg'))
            .pipe(minifyCSS({keepBreaks:false}))
            .pipe(concat('homepage-style.css'))
            .pipe(gulp.dest(config.cssTargetDest));
    });

    gulp.task('images', function() {
         gulp.src(config.source + '/img/**/*')
            .pipe(gulp.dest(config.destination + '/img'))
        return gulp.src(config.source + '/img/**/*').pipe(gulp.dest(config.destination + '/img'));
    });

    gulp.task('fonts', function() {
        return gulp.src(config.source + '/fonts/**/*').pipe(gulp.dest(config.destination + '/fonts'));
    });

    gulp.task('html', function() {
        gulp.src(config.source + '/components/**/*').pipe(gulp.dest(config.destination + '/components'));
        gulp.src(config.source + '/pages/**/*').pipe(gulp.dest(config.destination + '/pages'));
        gulp.src(config.topFolder + '/tweet_raw.json').pipe(gulp.dest(config.destination + '/tweets'));
        gulp.src(config.source + 'tweets/**/*').pipe(gulp.dest(config.destination + '/tweets'));
        return gulp.src(config.source + '/index.html').pipe(gulp.dest(config.destination));
    });

    gulp.task('bower', function() {
        return bower();
    });

    gulp.task('setUpSlick', function() {
        return gulp.src(config.jsLibraries)
            // .pipe($.count('## files', { logFiles: true }))
            .pipe(gulp.dest('./target/scripts/'));
    });

    gulp.task('slickCss', function() {
        return gulp.src(config.slickCss)
            // .pipe($.count('## files', { logFiles: true }))
            .pipe(gulp.dest('./target/css/'));
    });


    

    gulp.task('js', ['bower'], function() {
        //Ensure app.js comes first
        gulp.src(config.mainSrc + '/app.js')
            .pipe(sourcemaps.init({debug:true}))
            .pipe(concat('hermes-homepage.min.js'));
        var srcPipe = gulp.src(config.mainSrc)
            .pipe(sourcemaps.init({debug:true}))
            .pipe(concat('hermes-homepage.min.js'))
            .pipe(uglify())
            .pipe(sourcemaps.write('.'));
        var libPipe = gulp.src(bowerFiles({production: true}));

        return merge(srcPipe, libPipe)
            .pipe(gulp.dest(config.jsDest));
    });

    /**
     * Create $templateCache from the html templates
     * @return {Stream}
     */
    gulp.task('templatecache', function() {
        gutil.log('Creating an AngularJS $templateCache');

        return gulp
            .src(config.htmltemplates)
            .pipe($.if(args.verbose, $.bytediff.start()))
            .pipe($.minifyHtml({empty: true}))
            .pipe($.if(args.verbose, $.bytediff.stop(bytediffFormatter)))
            .pipe($.angularTemplatecache(
                config.templateCache.file,
                config.templateCache.options
            ))
            .pipe(gulp.dest(config.temp));
    });

    gulp.task('content', function() {
        return gulp.src(config.contentSrc)
        .pipe(gulp.dest(config.contentDest));
    });

    gulp.task('node', function() {
        return gulp.src(config.source + 'server.js')
        .pipe(gulp.dest(config.destination));
    });

    /**
     * Build tasks
     **/
    gulp.task('build', ['bower', 'styles', 'html', 'images', 'slickCss', 'setUpSlick', 'js', 'fonts', 'node', 'content'], function () {
    });

    gulp.task('webserver', ['styles', 'html'], function() {
        gulp.src('./target/')
            .pipe(webserver({
                livereload: true,
                directoryListing: false,
                open: true
            }));
    });

    gulp.task('build-and-run', ['build'], function() {
        gulp.watch(config.sassSrc, ['styles']);
        gulp.watch(config.mainSrc, ['js']);
        gulp.watch(config.source + '/**/*.html', ['html']);
        gulp.watch(config.contentSrc, ['content']);

        return gulp.src('./target/')
            .pipe(webserver({
                livereload: true,
                directoryListing: false,
                open: true,
                port: 8003,
                fallback: 'index.html'
            })
        );
    });
})();
