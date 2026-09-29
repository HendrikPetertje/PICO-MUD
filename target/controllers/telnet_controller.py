from models.storage import GameError
from controllers.session_controller import SessionController
from controllers.notification_controller import NotificationController
from controllers.command_controller import CommandController
from controllers.habit_controller import HabitController
from models.properties import Properties
from views import telnet_view


class TelnetController:
    def __init__(self, world):
        self.world = world
        self.properties = Properties()
        self.sessions = SessionController(world.users, world.rooms, self.properties)
        self.notifications = NotificationController(self.sessions)
        self.sessions.notifications = self.notifications
        self.commands = CommandController(world, self.sessions, self.notifications)
        self.habits = HabitController(world, self.sessions, self.notifications)

    def on_connect(self, client):
        session = self.sessions.new(client)
        session.reply(telnet_view.login())
        session.pump()

    def on_line(self, client, text):
        session = self.sessions.sessions[client]
        if client.closed or client.closing_at is not None:
            return
        if session.response is not None:
            if session.pending_name is None and text.strip().lower() == "/quit":
                self.sessions.kick(session, telnet_view.goodbye())
            else:
                session.busy = True
            return
        session.responding = True
        try:
            if session.playing and session.user_id is not None and session.user()["banned"]:
                self.sessions.kick(session, "You have been banned.\n")
                return
            if session.pending_name is not None:
                name = session.pending_name
                session.pending_name = None
                self.sessions.enter(session, name, text)
                result = self.commands.welcome(session)
            elif not text.strip():
                result = ""
            else:
                result = self.commands.dispatch(session, text.lstrip())
            if not client.closed and client.closing_at is None:
                if session.pending_name is not None:
                    session.reply("Password: ", prompt=False)
                elif result is not None:
                    session.reply(result)
        except GameError as error:
            session.reply(str(error) + "\n")
        finally:
            session.responding = False
        session.pump()

    def on_line_too_long(self, client):
        session = self.sessions.sessions[client]
        session.pending_name = None
        if session.response is not None:
            session.busy = True
        else:
            session.reply("Line too long; nothing executed.\n")
            session.pump()

    def on_reject(self, client, reason):
        client.close(telnet_view.server_full())

    def on_timeout(self, client):
        session = self.sessions.sessions.get(client)
        if session:
            self.sessions.kick(session, telnet_view.inactivity())
        else:
            client.close(telnet_view.inactivity())

    def on_disconnect(self, client, reason):
        self.sessions.disconnected(client)

    def on_tick(self, now_ms):
        self.habits.tick(self.world.tick(now_ms))
        for session in list(self.sessions.sessions.values()):
            if not session.client.closed and session.client.closing_at is None:
                session.pump()
