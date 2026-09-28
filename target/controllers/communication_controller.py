from models.storage import require, text
from views import game_view


class CommunicationController:
    def __init__(self, config, sessions, notifications):
        self.config, self.sessions, self.notifications = config, sessions, notifications

    def handle(self, session, verb, args):
        target = self.sessions.named(args.pop()) if verb in ("whisper", "page") else None
        message = text(args.rest(), self.config.MAX_TEXT_LENGTH, "Message")
        if verb == "shout":
            require(session.admin(), "Admin permission required.")
            self.notifications.everyone(game_view.speech(session.name(), message))
        elif target:
            require(verb != "whisper" or target.room_id == session.room_id, "Player is not in your room.")
            output = game_view.private_message(session.name(), target.name(), message, verb + "s")
            self.notifications.send(target, output)
            if target is not session:
                self.notifications.send(session, output)
        else:
            self.notifications.room(session.room_id, game_view.speech(session.name(), message, verb == "emote"))
        return ""
