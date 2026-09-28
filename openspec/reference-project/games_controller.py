import json
import time

from server import HEADERS_200_JSON, HEADERS_400, HEADERS_404, HEADERS_405, _send

# Shogi piece types
KING   = "K"
ROOK   = "R"
BISHOP = "B"
GOLD   = "G"
SILVER = "S"
KNIGHT = "N"
LANCE  = "L"
PAWN   = "P"

# Promoted versions
P_ROOK   = "+R"
P_BISHOP = "+B"
P_SILVER = "+S"
P_KNIGHT = "+N"
P_LANCE  = "+L"
P_PAWN   = "+P"

PROMOTABLE = {ROOK, BISHOP, SILVER, KNIGHT, LANCE, PAWN}
PROMOTED_MAP = {
    ROOK: P_ROOK, BISHOP: P_BISHOP, SILVER: P_SILVER,
    KNIGHT: P_KNIGHT, LANCE: P_LANCE, PAWN: P_PAWN,
}
UNPROMOTE_MAP = {v: k for k, v in PROMOTED_MAP.items()}

MAX_GAMES = 4
FORFEIT_TIMEOUT = 300   # 5 minutes no activity = forfeit
REMOVE_TIMEOUT  = 60    # 1 minute after forfeit = removed

# Starting board layout (from player 2's perspective, row 0 = top = player 2's back rank)
# Each cell: None or (owner, piece_type)
# owner: 1 or 2, piece_type: one of the constants above
# Standard shogi initial setup:
# Row 0: P2 back rank: L N S G K G S N L
# Row 1: P2 rook/bishop:  . R . . . . . B .
# Row 2: P2 pawns: P P P P P P P P P
# Row 6: P1 pawns
# Row 7: P1 bishop/rook: . B . . . . . R .
# Row 8: P1 back rank: L N S G K G S N L

def _initial_board():
    board = [[None]*9 for _ in range(9)]
    # Player 2 (top)
    back2 = [LANCE, KNIGHT, SILVER, GOLD, KING, GOLD, SILVER, KNIGHT, LANCE]
    for c in range(9):
        board[0][c] = (2, back2[c])
        board[2][c] = (2, PAWN)
    board[1][1] = (2, ROOK)
    board[1][7] = (2, BISHOP)
    # Player 1 (bottom)
    back1 = [LANCE, KNIGHT, SILVER, GOLD, KING, GOLD, SILVER, KNIGHT, LANCE]
    for c in range(9):
        board[8][c] = (1, back1[c])
        board[6][c] = (1, PAWN)
    board[7][7] = (1, ROOK)
    board[7][1] = (1, BISHOP)
    return board


def _moves_for_piece(owner, piece, r, c, board):
    """Return list of (row, col) squares this piece can move to."""
    moves = []
    # Direction multiplier: player 1 moves up (negative r), player 2 moves down (positive r)
    fwd = -1 if owner == 1 else 1

    def in_bounds(rr, cc):
        return 0 <= rr < 9 and 0 <= cc < 9

    def can_land(rr, cc):
        if not in_bounds(rr, cc):
            return False
        cell = board[rr][cc]
        return cell is None or cell[0] != owner

    def add_if_valid(rr, cc):
        if can_land(rr, cc):
            moves.append((rr, cc))

    def slide(dr, dc):
        rr, cc = r + dr, c + dc
        while in_bounds(rr, cc):
            cell = board[rr][cc]
            if cell is None:
                moves.append((rr, cc))
            else:
                if cell[0] != owner:
                    moves.append((rr, cc))
                break
            rr += dr
            cc += dc

    if piece == KING:
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                add_if_valid(r + dr, c + dc)

    elif piece == GOLD or piece in (P_SILVER, P_KNIGHT, P_LANCE, P_PAWN):
        # Gold moves: all adjacent except diagonal-backward
        for dc in (-1, 0, 1):
            add_if_valid(r + fwd, c + dc)  # forward row
        add_if_valid(r, c - 1)  # side
        add_if_valid(r, c + 1)  # side
        add_if_valid(r - fwd, c)  # straight back

    elif piece == SILVER:
        # Forward 3 and backward diagonals
        for dc in (-1, 0, 1):
            add_if_valid(r + fwd, c + dc)
        add_if_valid(r - fwd, c - 1)
        add_if_valid(r - fwd, c + 1)

    elif piece == KNIGHT:
        # Two forward, one to each side
        add_if_valid(r + 2*fwd, c - 1)
        add_if_valid(r + 2*fwd, c + 1)

    elif piece == LANCE:
        # Slides forward only
        slide(fwd, 0)

    elif piece == PAWN:
        add_if_valid(r + fwd, c)

    elif piece == ROOK:
        slide(-1, 0)
        slide(1, 0)
        slide(0, -1)
        slide(0, 1)

    elif piece == P_ROOK:
        # Dragon King: rook + 1 step diagonal
        slide(-1, 0)
        slide(1, 0)
        slide(0, -1)
        slide(0, 1)
        for dr in (-1, 1):
            for dc in (-1, 1):
                add_if_valid(r + dr, c + dc)

    elif piece == BISHOP:
        slide(-1, -1)
        slide(-1, 1)
        slide(1, -1)
        slide(1, 1)

    elif piece == P_BISHOP:
        # Dragon Horse: bishop + 1 step orthogonal
        slide(-1, -1)
        slide(-1, 1)
        slide(1, -1)
        slide(1, 1)
        for dr, dc in ((-1,0),(1,0),(0,-1),(0,1)):
            add_if_valid(r + dr, c + dc)

    return moves


def _can_promote(owner, piece, from_r, to_r):
    """Check if a piece can promote given move."""
    if piece not in PROMOTABLE:
        return False
    if piece == PAWN and piece in PROMOTED_MAP:
        pass  # pawns can promote
    # Promotion zone: rows 0-2 for player 1, rows 6-8 for player 2
    if owner == 1:
        return from_r <= 2 or to_r <= 2
    else:
        return from_r >= 6 or to_r >= 6


def _must_promote(owner, piece, to_r):
    """Check if promotion is mandatory (piece would be stuck)."""
    if piece == PAWN or piece == LANCE:
        if owner == 1 and to_r == 0:
            return True
        if owner == 2 and to_r == 8:
            return True
    if piece == KNIGHT:
        if owner == 1 and to_r <= 1:
            return True
        if owner == 2 and to_r >= 7:
            return True
    return False


def _drop_valid(owner, piece, r, c, board):
    """Validate a piece drop."""
    if board[r][c] is not None:
        return False
    # Cannot drop pawn on column that already has an unpromoted pawn of same owner
    if piece == PAWN:
        for row in range(9):
            cell = board[row][c]
            if cell and cell[0] == owner and cell[1] == PAWN:
                return False
    # Cannot drop into position where piece has no legal move
    fwd = -1 if owner == 1 else 1
    if piece == PAWN or piece == LANCE:
        if owner == 1 and r == 0:
            return False
        if owner == 2 and r == 8:
            return False
    if piece == KNIGHT:
        if owner == 1 and r <= 1:
            return False
        if owner == 2 and r >= 7:
            return False
    # Cannot drop pawn to give immediate checkmate (simplified: we skip this complex rule)
    return True


def _find_king(owner, board):
    for r in range(9):
        for c in range(9):
            cell = board[r][c]
            if cell and cell[0] == owner and cell[1] == KING:
                return (r, c)
    return None


def _is_in_check(owner, board):
    """Check if owner's king is threatened."""
    king_pos = _find_king(owner, board)
    if not king_pos:
        return True  # king captured = in check
    opp = 2 if owner == 1 else 1
    for r in range(9):
        for c in range(9):
            cell = board[r][c]
            if cell and cell[0] == opp:
                moves = _moves_for_piece(opp, cell[1], r, c, board)
                if king_pos in moves:
                    return True
    return False


def _board_to_json(board):
    """Convert board to JSON-friendly format."""
    result = []
    for row in board:
        r = []
        for cell in row:
            if cell is None:
                r.append(None)
            else:
                r.append([cell[0], cell[1]])
        result.append(r)
    return result


def _board_from_json(data):
    """Convert JSON board back to tuples."""
    board = []
    for row in data:
        r = []
        for cell in row:
            if cell is None:
                r.append(None)
            else:
                r.append((cell[0], cell[1]))
        r_list = r
        board.append(r_list)
    return board


class GamesController:
    def __init__(self):
        self.games = []
        self._next_id = 0

    def _cleanup(self):
        """Remove forfeited games past removal timeout."""
        now = time.time()
        # Mark forfeits
        for g in self.games:
            if g["status"] == "active" and now - g["last_activity"] > FORFEIT_TIMEOUT:
                g["status"] = "forfeit"
                g["forfeit_at"] = now
            elif g["status"] == "waiting" and now - g["last_activity"] > FORFEIT_TIMEOUT:
                g["status"] = "forfeit"
                g["forfeit_at"] = now
        # Remove old forfeits
        self.games = [g for g in self.games
                      if not (g["status"] == "forfeit" and now - g.get("forfeit_at", 0) > REMOVE_TIMEOUT)]

    def handle(self, conn, method, path, body):
        """Route /api/games/* requests."""
        self._cleanup()

        if path == "/api/games":
            if method == "GET":
                self._list_games(conn)
            else:
                _send(conn, HEADERS_405, "Method Not Allowed")

        elif path == "/api/games/create":
            if method == "POST":
                self._create_game(conn, body)
            else:
                _send(conn, HEADERS_405, "Method Not Allowed")

        elif path.startswith("/api/games/") and path.endswith("/join"):
            if method == "POST":
                game_id = self._extract_id(path, "/join")
                self._join_game(conn, body, game_id)
            else:
                _send(conn, HEADERS_405, "Method Not Allowed")

        elif path.startswith("/api/games/") and path.endswith("/move"):
            if method == "POST":
                game_id = self._extract_id(path, "/move")
                self._make_move(conn, body, game_id)
            else:
                _send(conn, HEADERS_405, "Method Not Allowed")

        elif path.startswith("/api/games/") and path.endswith("/drop"):
            if method == "POST":
                game_id = self._extract_id(path, "/drop")
                self._drop_piece(conn, body, game_id)
            else:
                _send(conn, HEADERS_405, "Method Not Allowed")

        elif path.startswith("/api/games/"):
            # GET /api/games/{id}
            if method == "GET":
                try:
                    game_id = int(path.split("/api/games/")[1])
                    self._get_game(conn, game_id)
                except (ValueError, IndexError):
                    _send(conn, HEADERS_404, "Not Found")
            else:
                _send(conn, HEADERS_405, "Method Not Allowed")

        else:
            _send(conn, HEADERS_404, "Not Found")

    def _extract_id(self, path, suffix):
        # /api/games/3/move -> 3
        part = path[len("/api/games/"):-len(suffix)]
        return int(part)

    def _list_games(self, conn):
        summary = []
        for g in self.games:
            summary.append({
                "id": g["id"],
                "p1": g["p1"],
                "p2": g["p2"],
                "status": g["status"],
                "turn": g["turn"],
            })
        _send(conn, HEADERS_200_JSON, json.dumps(summary))

    def _create_game(self, conn, body):
        if len(self.games) >= MAX_GAMES:
            _send(conn, HEADERS_400, '{"error":"too many active games"}')
            return
        try:
            payload = json.loads(body.decode())
            name = str(payload.get("name", "")).strip()[:10]
            if not name:
                _send(conn, HEADERS_400, '{"error":"name required"}')
                return
        except (ValueError, KeyError):
            _send(conn, HEADERS_400, '{"error":"invalid JSON"}')
            return

        self._next_id += 1
        # Randomly assign color: use time-based parity
        is_black = (self._next_id + int(time.time())) % 2 == 0

        game = {
            "id": self._next_id,
            "board": _initial_board(),
            "captured": {1: [], 2: []},
            "p1": name if is_black else None,
            "p2": name if not is_black else None,
            "p1_color": "black" if is_black else "white",
            "turn": 1,  # player 1 is always black (goes first in shogi)
            "status": "waiting",
            "last_activity": time.time(),
            "forfeit_at": None,
            "winner": None,
        }
        # Ensure p1 = black, p2 = white consistently
        # Rethink: p1 is always black, goes first. Creator assigned to p1 or p2.
        if is_black:
            game["p1"] = name
            game["p2"] = None
        else:
            game["p1"] = None
            game["p2"] = name

        self.games.append(game)
        _send(conn, HEADERS_200_JSON, json.dumps({
            "ok": True,
            "id": game["id"],
            "your_player": 1 if is_black else 2,
        }))

    def _join_game(self, conn, body, game_id):
        game = self._find_game(game_id)
        if not game:
            _send(conn, HEADERS_404, '{"error":"game not found"}')
            return
        if game["status"] != "waiting":
            _send(conn, HEADERS_400, '{"error":"game not available"}')
            return
        try:
            payload = json.loads(body.decode())
            name = str(payload.get("name", "")).strip()[:10]
            if not name:
                _send(conn, HEADERS_400, '{"error":"name required"}')
                return
        except (ValueError, KeyError):
            _send(conn, HEADERS_400, '{"error":"invalid JSON"}')
            return

        if game["p1"] is None:
            game["p1"] = name
            player_num = 1
        else:
            game["p2"] = name
            player_num = 2

        game["status"] = "active"
        game["last_activity"] = time.time()
        _send(conn, HEADERS_200_JSON, json.dumps({
            "ok": True,
            "your_player": player_num,
        }))

    def _get_game(self, conn, game_id):
        game = self._find_game(game_id)
        if not game:
            _send(conn, HEADERS_404, '{"error":"game not found"}')
            return
        resp = {
            "id": game["id"],
            "board": _board_to_json(game["board"]),
            "captured": {1: game["captured"][1], 2: game["captured"][2]},
            "p1": game["p1"],
            "p2": game["p2"],
            "turn": game["turn"],
            "status": game["status"],
            "winner": game["winner"],
        }
        _send(conn, HEADERS_200_JSON, json.dumps(resp))

    def _make_move(self, conn, body, game_id):
        game = self._find_game(game_id)
        if not game:
            _send(conn, HEADERS_404, '{"error":"game not found"}')
            return
        if game["status"] != "active":
            _send(conn, HEADERS_400, '{"error":"game not active"}')
            return
        try:
            payload = json.loads(body.decode())
            player = int(payload["player"])
            fr = int(payload["from_r"])
            fc = int(payload["from_c"])
            tr = int(payload["to_r"])
            tc = int(payload["to_c"])
            promote = bool(payload.get("promote", False))
        except (ValueError, KeyError, TypeError):
            _send(conn, HEADERS_400, '{"error":"invalid move data"}')
            return

        if player != game["turn"]:
            _send(conn, HEADERS_400, '{"error":"not your turn"}')
            return

        board = game["board"]
        cell = board[fr][fc]
        if not cell or cell[0] != player:
            _send(conn, HEADERS_400, '{"error":"no piece there"}')
            return

        piece = cell[1]
        valid_moves = _moves_for_piece(player, piece, fr, fc, board)
        if (tr, tc) not in valid_moves:
            _send(conn, HEADERS_400, '{"error":"illegal move"}')
            return

        # Simulate move and check if own king is in check
        target = board[tr][tc]
        board[fr][fc] = None
        board[tr][tc] = (player, piece)
        if _is_in_check(player, board):
            # Revert
            board[fr][fc] = (player, piece)
            board[tr][tc] = target
            _send(conn, HEADERS_400, '{"error":"move leaves king in check"}')
            return

        # Capture
        if target:
            captured_piece = target[1]
            # Unpromote captured piece
            if captured_piece in UNPROMOTE_MAP:
                captured_piece = UNPROMOTE_MAP[captured_piece]
            game["captured"][player].append(captured_piece)

        # Promotion
        if promote and _can_promote(player, piece, fr, tr):
            board[tr][tc] = (player, PROMOTED_MAP[piece])
        elif _must_promote(player, piece, tr):
            board[tr][tc] = (player, PROMOTED_MAP[piece])

        # Check if opponent king is captured (win condition)
        opp = 2 if player == 1 else 1
        if _find_king(opp, board) is None:
            game["status"] = "finished"
            game["winner"] = player

        # Switch turn
        game["turn"] = opp
        game["last_activity"] = time.time()

        _send(conn, HEADERS_200_JSON, '{"ok":true}')

    def _drop_piece(self, conn, body, game_id):
        game = self._find_game(game_id)
        if not game:
            _send(conn, HEADERS_404, '{"error":"game not found"}')
            return
        if game["status"] != "active":
            _send(conn, HEADERS_400, '{"error":"game not active"}')
            return
        try:
            payload = json.loads(body.decode())
            player = int(payload["player"])
            piece = str(payload["piece"])
            tr = int(payload["to_r"])
            tc = int(payload["to_c"])
        except (ValueError, KeyError, TypeError):
            _send(conn, HEADERS_400, '{"error":"invalid drop data"}')
            return

        if player != game["turn"]:
            _send(conn, HEADERS_400, '{"error":"not your turn"}')
            return

        if piece not in game["captured"][player]:
            _send(conn, HEADERS_400, '{"error":"piece not in hand"}')
            return

        board = game["board"]
        if not _drop_valid(player, piece, tr, tc, board):
            _send(conn, HEADERS_400, '{"error":"illegal drop"}')
            return

        # Place piece and check it doesn't leave king in check
        board[tr][tc] = (player, piece)
        if _is_in_check(player, board):
            board[tr][tc] = None
            _send(conn, HEADERS_400, '{"error":"drop leaves king in check"}')
            return

        game["captured"][player].remove(piece)

        # Switch turn
        opp = 2 if player == 1 else 1
        game["turn"] = opp
        game["last_activity"] = time.time()

        _send(conn, HEADERS_200_JSON, '{"ok":true}')

    def _find_game(self, game_id):
        for g in self.games:
            if g["id"] == game_id:
                return g
        return None
