import json

from server import HEADERS_200_JSON, HEADERS_400, HEADERS_405, _send

MAX_MESSAGES = 20
MAX_USERNAME = 10
MAX_MESSAGE  = 250


class MessagesController:
    def __init__(self):
        self.messages   = []
        self._message_id = 0

    def add_message(self, username, text):
        username = username[:MAX_USERNAME]
        text = text[:MAX_MESSAGE]
        self._message_id += 1
        self.messages.append({"id": self._message_id, "u": username, "m": text})
        if len(self.messages) > MAX_MESSAGES:
            self.messages.pop(0)

    def handle(self, conn, method, body):
        """Route /api/messages GET and POST requests."""
        if method == "GET":
            self._get_messages(conn)
        elif method == "POST":
            self._post_message(conn, body)
        else:
            _send(conn, HEADERS_405, "Method Not Allowed")

    def _get_messages(self, conn):
        _send(conn, HEADERS_200_JSON, json.dumps(self.messages))

    def _post_message(self, conn, body):
        try:
            payload = json.loads(body.decode())
            username = str(payload.get("u", "")).strip()
            text = str(payload.get("message", "")).strip()
            if not username or not text:
                _send(conn, HEADERS_400, '{"error":"u and message are required"}')
                return
            self.add_message(username, text)
            _send(conn, HEADERS_200_JSON, '{"ok":true}')
        except (ValueError, KeyError) as e:
            _send(conn, HEADERS_400, json.dumps({"error": "invalid JSON: {}".format(e)}))
