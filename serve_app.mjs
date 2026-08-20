import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import url from "node:url";

const ROOT = path.dirname(url.fileURLToPath(import.meta.url));
const PORT = 8765;

const MIME_TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".ico": "image/x-icon",
  ".txt": "text/plain; charset=utf-8"
};

function send(res, statusCode, body, contentType = "text/plain; charset=utf-8") {
  res.writeHead(statusCode, {
    "Content-Type": contentType,
    "Cache-Control": "no-store"
  });
  res.end(body);
}

function safePathFromRequest(requestUrl) {
  const parsed = new url.URL(requestUrl, `http://127.0.0.1:${PORT}`);
  let pathname = decodeURIComponent(parsed.pathname);
  if (pathname === "/") pathname = "/index.html";
  const resolved = path.resolve(ROOT, `.${pathname}`);
  if (!resolved.startsWith(ROOT)) {
    return null;
  }
  return resolved;
}

const server = http.createServer((req, res) => {
  const filePath = safePathFromRequest(req.url || "/");
  if (!filePath) {
    send(res, 403, "Forbidden");
    return;
  }

  fs.stat(filePath, (statError, stats) => {
    if (statError || !stats.isFile()) {
      send(res, 404, "Not found");
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || "application/octet-stream";
    const stream = fs.createReadStream(filePath);

    res.writeHead(200, {
      "Content-Type": contentType,
      "Cache-Control": "no-store"
    });

    stream.on("error", () => send(res, 500, "Server error"));
    stream.pipe(res);
  });
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`NFL app running at http://127.0.0.1:${PORT}/`);
});

server.on("error", (error) => {
  console.error("Failed to start NFL app server.");
  console.error(error.message);
  process.exit(1);
});
