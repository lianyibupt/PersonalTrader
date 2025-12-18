import os
import json
import logging
from http.server import BaseHTTPRequestHandler, HTTPServer
import requests


logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _rewrite_tool_choice(payload):
    value = payload.get("tool_choice")
    if isinstance(value, dict):
        payload["tool_choice"] = "auto"
    return payload


class OpenAIProxyHandler(BaseHTTPRequestHandler):
    def _get_upstream_config(self):
        base = os.getenv("UPSTREAM_OPENAI_BASE_URL") or os.getenv("OPENAI_BASE_URL") or "http://127.0.0.1:1234/v1"
        key = os.getenv("UPSTREAM_OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY") or "local"
        return base.rstrip("/"), key

    def _forward(self, method):
        upstream_base, upstream_key = self._get_upstream_config()
        length = int(self.headers.get("Content-Length", "0") or "0")
        body = self.rfile.read(length) if length > 0 else b""
        url = upstream_base + self.path
        headers = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "content-length", "connection")}
        auth = self.headers.get("Authorization")
        if not auth and upstream_key:
            headers["Authorization"] = f"Bearer {upstream_key}"
        if method == "POST" and self.path.startswith("/v1/chat/completions"):
            try:
                data = json.loads(body.decode("utf-8")) if body else {}
            except Exception:
                data = {}
            data = _rewrite_tool_choice(data)
            resp = requests.post(url, headers=headers, json=data)
        else:
            if method == "POST":
                resp = requests.post(url, headers=headers, data=body)
            elif method == "GET":
                resp = requests.get(url, headers=headers, data=body)
            else:
                resp = requests.request(method, url, headers=headers, data=body)
        content = resp.content
        self.send_response(resp.status_code)
        ctype = resp.headers.get("Content-Type", "application/json")
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        try:
            self._forward("POST")
        except Exception as e:
            logger.error(f"Proxy POST error: {e}")
            message = json.dumps({"error": str(e)}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)

    def do_GET(self):
        try:
            self._forward("GET")
        except Exception as e:
            logger.error(f"Proxy GET error: {e}")
            message = json.dumps({"error": str(e)}).encode("utf-8")
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(message)))
            self.end_headers()
            self.wfile.write(message)


def run():
    host = os.getenv("OPENAI_PROXY_HOST", "127.0.0.1")
    port = int(os.getenv("OPENAI_PROXY_PORT", "8001"))
    server = HTTPServer((host, port), OpenAIProxyHandler)
    logger.info(f"OpenAI proxy listening on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()

