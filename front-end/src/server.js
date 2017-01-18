var http = require("http"),
    url = require("url"),
    path = require("path"),
    fs = require("fs")
    querystring = require('querystring')
    port = process.argv[2] || 8888;

http.createServer(function(request, response) {
	if (request.method == 'POST') {
        var body = '';
		var decodedBody = '';
        request.on('data', function (data) {
            body += data;
            console.log("Partial body: " + body);
        });
        request.on('end', function () {
            console.log("Body: " + body);
			decodedBody = querystring.parse(body);
			var uri = url.parse(request.url).pathname
			, filename = path.join(process.cwd(), uri) + decodedBody.filename;
			
			fs.writeFile(filename, "Hey there!", function(err) {
				if(err) {
					return console.log(err);
				}

				console.log("The file was saved!");
			}); 
        });
        response.writeHead(200, {'Content-Type': 'text/html'});
        response.end('post received');
    }
    else
    {
		var uri = url.parse(request.url).pathname
		, filename = path.join(process.cwd(), uri);
	  
		fs.exists(filename, function(exists) {
			if(!exists) {
				response.writeHead(404, {"Content-Type": "text/plain"});
				response.write("404 Not Found\n");
				response.end();
				return;
			}

			if (fs.statSync(filename).isDirectory()) filename += '/index.html';

			fs.readFile(filename, "binary", function(err, file) {
				if(err) {        
					response.writeHead(500, {"Content-Type": "text/plain"});
					response.write(err + "\n");
					response.end();
					return;
				}

				response.writeHead(200);
				response.write(file, "binary");
				response.end();
			});
		});
	}
}).listen(parseInt(port, 10));

console.log("Static file server running at\n  => http://localhost:" + port + "/\nCTRL + C to shutdown");