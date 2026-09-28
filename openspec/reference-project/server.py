import socket
import uselect
import uos
import time
import gc



MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css",
    ".js": "application/javascript",
    ".json": "application/json",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".ico": "image/x-icon",
}


def _mime_for(path):
    for ext, mime in MIME_TYPES.items():
        if path.endswith(ext):
            return mime
    return "application/octet-stream"

HTTP_ROOT = "http"

HEADERS_200_HTML = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: text/html; charset=utf-8\r\n"
    "Connection: close\r\n"
)

HEADERS_200_JSON = (
    "HTTP/1.1 200 OK\r\n"
    "Content-Type: application/json\r\n"
    "Connection: close\r\n"
)

HEADERS_400 = (
    "HTTP/1.1 400 Bad Request\r\n"
    "Content-Type: application/json\r\n"
    "Connection: close\r\n"
)

HEADERS_404 = (
    "HTTP/1.1 404 Not Found\r\n"
    "Content-Type: text/plain\r\n"
    "Connection: close\r\n"
)

HEADERS_405 = (
    "HTTP/1.1 405 Method Not Allowed\r\n"
    "Content-Type: text/plain\r\n"
    "Connection: close\r\n"
)

HEADERS_302 = (
    "HTTP/1.1 302 Found\r\n"
    "Content-Type: text/html; charset=utf-8\r\n"
    "Location: http://192.168.4.1/\r\n"
    "Connection: close\r\n"
)

# Captive portal detection paths — respond with redirect to trigger portal popup
CAPTIVE_PATHS = frozenset([
    "/generate_204", "/gen_204", "/ncsi.txt",
    "/hotspot-detect.html", "/library/test/success.html",
    "/connecttest.txt", "/redirect", "/success.txt",
    "/canonical.html", "/favicon.ico",
])

MAX_HEADER_SIZE = 4096   # bytes; cap unbounded header reads
MAX_BODY_SIZE   = 1024   # bytes; cap POST body
CONN_TIMEOUT    = 10     # seconds; drop slow/hung clients
MAX_CLIENTS     = 6      # max simultaneous connections


def _send(conn, headers, body):
    if isinstance(body, str):
        body = body.encode()
    response = (headers + "Content-Length: {}\r\n\r\n".format(len(body))).encode() + body
    conn.sendall(response)


def _parse_buf(buf):
    """Parse a complete HTTP request from a buffer. Returns (method, path, body) or (None, None, None)."""
    if b"\r\n\r\n" not in buf:
        return None, None, None

    header_part, _, rest = buf.partition(b"\r\n\r\n")
    lines = header_part.decode().split("\r\n")
    request_line = lines[0].split()

    if len(request_line) < 2:
        return None, None, b""

    method = request_line[0]
    path = request_line[1].split("?")[0]

    content_length = 0
    for line in lines[1:]:
        if line.lower().startswith("content-length:"):
            try:
                content_length = min(int(line.split(":", 1)[1].strip()), MAX_BODY_SIZE)
            except ValueError:
                pass

    if len(rest) < content_length:
        return None, None, None  # body not yet fully received

    return method, path, rest[:content_length]


class HTTPServer:
    def __init__(self, messages_controller, games_controller=None, square_controller=None):
        self.messages_controller = messages_controller
        self.games_controller = games_controller
        self.square_controller = square_controller

    def _dispatch(self, conn, method, path, body):
        print(method, path)

        if path.startswith("/api/"):
            self._dispatch_api(conn, method, path, body)
        else:
            if method != "GET":
                _send(conn, HEADERS_405, "Method Not Allowed")
            else:
                self._serve_file(conn, path)

    def _dispatch_api(self, conn, method, path, body):
        if path == "/api/messages":
            self.messages_controller.handle(conn, method, body)
        elif path.startswith("/api/games") and self.games_controller:
            self.games_controller.handle(conn, method, path, body)
        elif path.startswith("/api/square") and self.square_controller:
            self.square_controller.handle(conn, method, path, body)
        else:
            _send(conn, HEADERS_404, "Not Found")

    def _serve_file(self, conn, path):
        # Normalise: "/" -> "/index.html"
        if path == "/":
            path = "/index.html"

        # Captive portal probes — minimal redirect to trigger portal popup
        if path in CAPTIVE_PATHS:
            _send(conn, HEADERS_302, "<html><body><a href='http://192.168.4.1/'>here</a></body></html>")
            return

        # Reject any path that tries to escape the http root
        if ".." in path:
            _send(conn, HEADERS_404, "Not Found")
            return

        file_path = HTTP_ROOT + path
        if not self._stream_file(conn, file_path):
            _send(conn, HEADERS_404, "Not Found")

    def _stream_file(self, conn, file_path):
        try:
            size = uos.stat(file_path)[6]
        except OSError:
            return False
        mime = _mime_for(file_path)
        # Cache static assets aggressively (images indefinitely, HTML for 60s)
        if mime.startswith("image/"):
            cache = "Cache-Control: public, max-age=86400\r\n"
        elif mime.startswith("text/html"):
            cache = "Cache-Control: public, max-age=60\r\n"
        else:
            cache = "Cache-Control: public, max-age=3600\r\n"
        header = "HTTP/1.1 200 OK\r\nContent-Type: {}\r\n{}Connection: close\r\nContent-Length: {}\r\n\r\n".format(mime, cache, size)
        try:
            conn.sendall(header.encode())
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(2048)
                    if not chunk:
                        break
                    conn.sendall(chunk)
                    time.sleep_ms(2)  # yield to network stack
        except OSError:
            pass  # client disconnected mid-transfer, that's ok
        return True

    def run(self):
        srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", 80))
        srv.listen(8)
        srv.setblocking(False)

        poll = uselect.poll()
        poll.register(srv, uselect.POLLIN)

        # clients: conn -> (recv_buf, opened_at)
        clients = {}

        print("HTTP server running")

        gc_counter = 0

        while True:
            try:
                events = poll.poll(100)
            except Exception as e:
                print("poll error:", e)
                continue

            now = time.time()
            gc_counter += 1
            if gc_counter >= 50:  # every ~5 seconds
                gc.collect()
                gc_counter = 0

            for obj, event in events:
                if obj is srv:
                    # New incoming connection
                    try:
                        conn, addr = srv.accept()
                        if len(clients) >= MAX_CLIENTS:
                            conn.close()
                            continue
                        conn.setblocking(False)
                        poll.register(conn, uselect.POLLIN)
                        clients[conn] = (b"", now)
                    except Exception as e:
                        print("accept error:", e)
                else:
                    conn = obj
                    if conn not in clients:
                        poll.unregister(conn)
                        conn.close()
                        continue

                    buf, opened_at = clients[conn]

                    # Read available data
                    try:
                        chunk = conn.recv(1024)
                    except OSError:
                        chunk = b""

                    if not chunk:
                        # Client disconnected
                        poll.unregister(conn)
                        del clients[conn]
                        conn.close()
                        continue

                    buf += chunk
                    if len(buf) > MAX_HEADER_SIZE + MAX_BODY_SIZE:
                        # Request too large
                        poll.unregister(conn)
                        del clients[conn]
                        conn.close()
                        continue

                    method, path, body = _parse_buf(buf)

                    if method is None and path is None and body is None:
                        # Incomplete request, keep buffering
                        clients[conn] = (buf, opened_at)
                        continue

                    # Complete request — dispatch and close
                    poll.unregister(conn)
                    del clients[conn]
                    try:
                        if method is None:
                            _send(conn, HEADERS_400, '{"error":"bad request"}')
                        else:
                            self._dispatch(conn, method, path, body)
                    except Exception as e:
                        print("Handler error:", e)
                    finally:
                        conn.close()

            # Evict timed-out connections
            now = time.time()
            stale = [c for c, (_, t) in clients.items() if now - t > CONN_TIMEOUT]
            for conn in stale:
                poll.unregister(conn)
                del clients[conn]
                conn.close()
