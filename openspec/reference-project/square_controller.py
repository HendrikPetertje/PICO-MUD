import json
import time

from server import HEADERS_200_JSON, HEADERS_400, HEADERS_405, _send

MAX_PLAYERS = 12
MAX_CHAT = 30
MAX_MSG_LEN = 120
PLAYER_TIMEOUT = 20  # seconds before player removed

# World bounds (in pixels) — background is 1254x1254
WORLD_W = 1254
WORLD_H = 1254


class SquareController:
    def __init__(self):
        self.players = {}  # name -> {x, y, char, last_seen}
        self.chat = []  # [{id, u, m, t}]
        self._chat_id = 0

    def _cleanup(self):
        now = time.time()
        stale = [n for n, p in self.players.items() if now - p["last_seen"] > PLAYER_TIMEOUT]
        for n in stale:
            del self.players[n]

    def handle(self, conn, method, path, body):
        if path == "/api/square/join":
            self._join(conn, method, body)
        elif path == "/api/square/move":
            self._move(conn, method, body)
        elif path == "/api/square/state":
            self._state(conn, method)
        elif path == "/api/square/chat":
            self._chat_handler(conn, method, body)
        else:
            _send(conn, HEADERS_400, '{"error":"unknown square endpoint"}')

    def _join(self, conn, method, body):
        if method != "POST":
            _send(conn, HEADERS_405, "Method Not Allowed")
            return
        try:
            data = json.loads(body.decode())
            name = str(data.get("name", "")).strip()[:10]
            char = int(data.get("char", 1))
            if not name or char < 1 or char > 8:
                _send(conn, HEADERS_400, '{"error":"name and char(1-8) required"}')
                return
            self._cleanup()
            if name not in self.players and len(self.players) >= MAX_PLAYERS:
                _send(conn, HEADERS_400, '{"error":"square is full"}')
                return
            # Spawn in middle of walkable area
            spawn_x = WORLD_W // 2
            spawn_y = 900
            if name in self.players:
                # Keep position
                spawn_x = self.players[name]["x"]
                spawn_y = self.players[name]["y"]
            self.players[name] = {"x": spawn_x, "y": spawn_y, "tx": spawn_x, "ty": spawn_y, "char": char, "last_seen": time.time()}
            _send(conn, HEADERS_200_JSON, json.dumps({"ok": True}))
        except (ValueError, KeyError) as e:
            _send(conn, HEADERS_400, json.dumps({"error": str(e)}))

    def _move(self, conn, method, body):
        if method != "POST":
            _send(conn, HEADERS_405, "Method Not Allowed")
            return
        try:
            data = json.loads(body.decode())
            name = str(data.get("name", "")).strip()[:10]
            x = int(data.get("x", 0))
            y = int(data.get("y", 0))
            if name not in self.players:
                _send(conn, HEADERS_400, '{"error":"not joined"}')
                return
            # Clamp to world bounds
            x = max(0, min(x, WORLD_W))
            y = max(300, min(y, WORLD_H - 30))  # can't walk into water (top 300px)
            self.players[name]["tx"] = x
            self.players[name]["ty"] = y
            self.players[name]["last_seen"] = time.time()
            _send(conn, HEADERS_200_JSON, '{"ok":true}')
        except (ValueError, KeyError) as e:
            _send(conn, HEADERS_400, json.dumps({"error": str(e)}))

    def _state(self, conn, method):
        if method != "GET":
            _send(conn, HEADERS_405, "Method Not Allowed")
            return
        self._cleanup()
        players = []
        for name, p in self.players.items():
            players.append({"name": name, "x": p["x"], "y": p["y"], "tx": p["tx"], "ty": p["ty"], "char": p["char"]})
        _send(conn, HEADERS_200_JSON, json.dumps({"players": players, "chat": self.chat}))

    def _chat_handler(self, conn, method, body):
        if method != "POST":
            _send(conn, HEADERS_405, "Method Not Allowed")
            return
        try:
            data = json.loads(body.decode())
            name = str(data.get("name", "")).strip()[:10]
            msg = str(data.get("m", "")).strip()[:MAX_MSG_LEN]
            if not name or not msg:
                _send(conn, HEADERS_400, '{"error":"name and m required"}')
                return
            if name not in self.players:
                _send(conn, HEADERS_400, '{"error":"not joined"}')
                return
            self.players[name]["last_seen"] = time.time()
            self._chat_id += 1
            self.chat.append({"id": self._chat_id, "u": name, "m": msg, "t": time.time()})
            if len(self.chat) > MAX_CHAT:
                self.chat.pop(0)
            _send(conn, HEADERS_200_JSON, '{"ok":true}')
        except (ValueError, KeyError) as e:
            _send(conn, HEADERS_400, json.dumps({"error": str(e)}))
