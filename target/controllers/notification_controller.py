from views import game_view


class NotificationController:
    def __init__(self, sessions):
        self.sessions = sessions

    def send(self, session, message):
        if not session.playing or session.client.closed or session.client.closing_at is not None:
            return False
        try:
            output = game_view.notification(message, not session.responding and session.response is None)
            if session.client.try_send(output):
                return True
            session.missed = True
        except OSError:
            session.missed = True
        return False

    def user(self, user_id, message):
        session = self.sessions.by_user.get(user_id)
        return self.send(session, message) if session else False

    def room(self, room_id, message, exclude=None):
        for session in self.sessions.live():
            if session.room_id == room_id and session is not exclude:
                self.send(session, message)

    def everyone(self, message):
        for session in self.sessions.live():
            self.send(session, message)
