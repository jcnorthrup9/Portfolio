const http = require("http");
const fs = require("fs");
const path = require("path");

const root = __dirname;
const port = 8420;

const types = {
  ".html": "text/html",
  ".css": "text/css",
  ".js": "text/javascript",
  ".svg": "image/svg+xml",
};

http.createServer((req, res) => {
  let reqPath = decodeURIComponent(req.url.split("?")[0]);
  if (reqPath.endsWith("/")) reqPath += "index.html";
  const filePath = path.join(root, reqPath);

  fs.readFile(filePath, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end("Not found: " + reqPath);
      return;
    }
    const ext = path.extname(filePath);
    res.writeHead(200, { "Content-Type": types[ext] || "application/octet-stream" });
    res.end(data);
  });
}).listen(port, () => console.log(`Serving ${root} at http://localhost:${port}`));
