/**
 * TechNova Employee Management System — AI Studio Bridge Server
 * Spawns the Flask Python backend on port 5000 and reverse proxies port 3000 traffic.
 * This enables the Flask Jinja2 application to render directly in the AI Studio preview.
 */

import http from "node:http";
import { spawn } from "node:child_process";
import path from "node:path";

const FLASK_PORT = 5000;
const PROXY_PORT = parseInt(process.env.PORT || "3000", 10);

console.log("[Bridge] Starting Flask application on port", FLASK_PORT);

const flaskProcess = spawn("python3", ["app.py"], {
  cwd: path.resolve(__dirname),
  env: {
    ...process.env,
    PORT: String(FLASK_PORT),
    FLASK_DEBUG: "0",
  },
  stdio: "inherit",
});

flaskProcess.on("error", (err) => {
  console.error("[Bridge] Failed to start Flask process:", err);
});

flaskProcess.on("exit", (code, signal) => {
  console.log(`[Bridge] Flask process exited with code ${code} and signal ${signal}`);
});

// Proxy HTTP requests to Flask
const server = http.createServer((clientReq, clientRes) => {
  const options = {
    hostname: "127.0.0.1",
    port: FLASK_PORT,
    path: clientReq.url,
    method: clientReq.method,
    headers: clientReq.headers,
  };

  const proxyReq = http.request(options, (flaskRes) => {
    clientRes.writeHead(flaskRes.statusCode || 200, flaskRes.headers);
    flaskRes.pipe(clientRes, { end: true });
  });

  proxyReq.on("error", (err) => {
    console.error("[Bridge] Proxy connection error:", err.message);
    clientRes.writeHead(502, { "Content-Type": "text/html" });
    clientRes.end(`
      <html>
        <body style="font-family:sans-serif;padding:2rem;text-align:center;">
          <h2>Starting TechNova Flask Application...</h2>
          <p>The Python backend is initializing. Please refresh in a few seconds.</p>
        </body>
      </html>
    `);
  });

  clientReq.pipe(proxyReq, { end: true });
});

server.listen(PROXY_PORT, "0.0.0.0", () => {
  console.log(`[Bridge] Proxy server listening on http://0.0.0.0:${PROXY_PORT} -> http://127.0.0.1:${FLASK_PORT}`);
});

process.on("SIGINT", () => {
  flaskProcess.kill("SIGINT");
  process.exit();
});

process.on("SIGTERM", () => {
  flaskProcess.kill("SIGTERM");
  process.exit();
});
