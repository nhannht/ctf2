from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import quote, urlsplit


DEFAULT_TARGET = (
    "http://%EF%BD%89%EF%BD%8E%EF%BD%94%EF%BD%85%EF%BD%92"
    "%EF%BD%8E%EF%BD%81%EF%BD%8C:8080/api/me"
)


class RedirectHandler(BaseHTTPRequestHandler):
    def send_redirect(self):
        query = urlsplit(self.path).query
        target = DEFAULT_TARGET
        for part in query.split("&"):
            if part.startswith("to="):
                target = part[3:] or DEFAULT_TARGET
                break
        target = quote(target, safe=":/?&=%#[]@!$'()*+,;")
        self.send_response(307)
        self.send_header("Location", target)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        self.send_redirect()

    def do_POST(self):
        self.send_redirect()

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 18080), RedirectHandler).serve_forever()
