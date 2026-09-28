from models.storage import require, GameError
from views import game_view


class Session:
    def __init__(self, client, users, rooms):
        self.client, self.users = client, users
        self.rooms = rooms
        self.user_id = None
        self.guest_name = None
        self.room_id = None
        self.pending_name = None
        self.playing = False
        self.response = None
        self.pending_chunk = None
        self.busy = False
        self.missed = False
        self.responding = False
        self.response_room = None
        self.response_admin = False

    def user(self):
        return self.users.get(self.user_id) if self.user_id is not None else None

    def admin(self):
        user = self.user()
        return bool(user and user["admin"])

    def name(self):
        user = self.user()
        return user["name"] if user is not None else self.guest_name

    def can_enter(self, room):
        return not room["private"] or self.user_id == room["owner_id"] or self.admin()

    def can_edit(self, room):
        return self.playing and self.user_id is not None and (self.user_id == room["owner_id"] or self.admin())

    def reply(self, lines, prompt=True):
        self.response = game_view.chunks(lines, prompt)
        self.pending_chunk = None
        self.response_room = self.room_id
        self.response_admin = self.admin() if self.playing else False

    def cancel(self):
        self.response = None
        self.pending_chunk = None
        self.pending_name = None
        self.busy = False
        self.missed = False

    def pump(self):
        if self.response is not None and self.playing:
            if self.response_room != self.room_id or (self.response_admin and not self.admin()):
                self.reply("Your location or permissions changed; please retry.\n")
        for _ in range(4):
            if self.response is None:
                break
            if self.pending_chunk is None:
                try:
                    self.pending_chunk = next(self.response)
                except StopIteration:
                    self.response = None
                    break
                except GameError as error:
                    self.response = game_view.chunks((str(error) + "\n",))
                    continue
            chunk = self.pending_chunk
            terminal = False
            if type(chunk) is tuple:
                chunk, room_id = chunk
                terminal = room_id is None
                if not terminal and (not self.rooms.has(room_id) or not self.can_enter(self.rooms.get(room_id))):
                    self.pending_chunk = None
                    continue
            if not self.client.try_send(chunk):
                return
            self.pending_chunk = None
            if terminal:
                self.response = None
                break
        if self.response is None and (self.busy or self.missed):
            message = "Previous input was ignored while output was busy. Please retry." if self.busy else "Some notifications were missed while output was busy."
            if self.client.try_send(game_view.notification(message, self.pending_name is None)):
                self.busy = self.missed = False


class SessionController:
    def __init__(self, users, rooms):
        self.users = users
        self.rooms = rooms
        self.sessions = {}
        self.by_user = {}
        self.guest_counter = 0
        self.notifications = None

    def new(self, client):
        session = Session(client, self.users, self.rooms)
        self.sessions[client] = session
        return session

    def live(self):
        return [s for s in self.sessions.values()
                if s.playing and not s.client.closed and s.client.closing_at is None]

    def named(self, name):
        for session in self.live():
            if session.name().lower() == name.lower():
                return session
        raise GameError("Player is not online.")

    def enter(self, session, name, password=None):
        require(not session.playing, "Disconnect before changing identity.")
        if name.lower() == "guest":
            require(password is None, "Guest login takes no password.")
            self.guest_counter += 1
            session.guest_name = "guest-" + str(self.guest_counter)
        else:
            user = self.users.authenticate(name, password)
            require(user is not None, "Login failed.")
            previous = self.by_user.get(user["user_id"])
            if previous is not None:
                self.kick(previous, "Replaced by a new login.\n")
            session.user_id = user["user_id"]
            self.by_user[session.user_id] = session
        session.pending_name = None
        session.room_id = 1
        session.playing = True
        if self.notifications:
            self.notifications.room(1, game_view.presence(session.name(), "arrives"), session)

    def remove(self, session):
        if session.playing:
            room_id, name = session.room_id, session.name()
            session.playing = False
            if self.by_user.get(session.user_id) is session:
                del self.by_user[session.user_id]
            if self.notifications:
                self.notifications.room(room_id, game_view.presence(name, "leaves"), session)
        session.cancel()

    def kick(self, session, message):
        self.remove(session)
        # Drop obsolete queued presentation so the reason can fit before close.
        session.client.output = bytearray()
        session.client.close(message)

    def disconnected(self, client):
        session = self.sessions.pop(client, None)
        if session:
            self.remove(session)
