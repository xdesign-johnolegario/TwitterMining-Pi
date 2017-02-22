module.exports = function() {
    'use strict';
    var path = require('path'),
        dest = path.join(__dirname, '../target'),
        partialsPrefix = path.join(__dirname, '../src/scripts');
    var temp = './.tmp/';

    return {
        source: path.join(__dirname, '../src'),
        topFolder: path.join(__dirname, '../'),
        destination: dest,
        sassSrc: path.join(__dirname, '../src/sass/**/*.scss'),
        mainSrc: path.join(__dirname, '../src/scripts/**/*.js'),
        testSrc: path.join(__dirname, '../tests/**/*.js'),
        contentSrc: path.join(__dirname, '../src/content/**/*.json'),



        jsLibraries: [
            './node_modules/angular-slick-carousel/dist/angular-slick.min.js',
            './bower_components/slick-carousel/slick/slick.min.js'
        ],

        slickCss: [
            './bower_components/slick-carousel/slick/slick-theme.css',
            './bower_components/slick-carousel/slick/slick.css'
        ],

        //CMS
        cmsSrc: path.join(__dirname, '../cms/src'),
        cmsSassSrc: path.join(__dirname, '../cms/src/sass/**/*.scss'),
        cmsMainSrc: path.join(__dirname, '../cms/src/scripts/**/*.js'),
        cmsPageSrc: path.join(__dirname, '../cms/src/pages/**/*.html'),
        cmsComponentsSrc: path.join(__dirname, '../cms/src/components/**/*.html'),

        //TODO: should be under target/ but this causes font-awesome path issues
        cssDest: path.join(__dirname, '../src/css'),
        cssTargetDest: path.join(__dirname, '../target/css'),
        devLib: path.join(__dirname, '../bower_components'),
        jsDest: path.join(dest, 'scripts'),
        contentDest: path.join(dest, 'content'),
        htmltemplates: path.join(__dirname, '../src/components/**/*.html'),

        cmsDest: path.join(__dirname, '../cms/target'),
        cmsCssTargetDest: path.join(__dirname, '../cms/target/css'),
        cmsJsTargetDest: path.join(__dirname, '../cms/target/scripts'),
        cmsPageTargetDest: path.join(__dirname, '../cms/target/pages'),
        cmsComponentsTargetDest: path.join(__dirname, '../cms/target/components'),

        partialsSrc: path.join(partialsPrefix, 'partials/**/*.html'),
        sassBase: path.join(__dirname, '../src/main/webapp/designers'),
        partialsPrefix: partialsPrefix,
        magnoliaAuth: 'Basic c3VwZXJ1c2VyOnN1cGVydXNlcg==',
        templateCache: {
            file: 'templates.js',
            options: {
                module: 'UxDesigns',
                root: 'components/',
                standalone: false
            }
        },
        temp: temp
    };
}();