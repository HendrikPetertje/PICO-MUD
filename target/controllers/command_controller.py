from models.storage import require, GameError
from models.rooms import DIRECTIONS
from modules.commands import COMMANDS, REGISTRY
from modules.command_parser import Arguments
from controllers.room_controller import RoomController
from controllers.item_controller import ItemController
from controllers.communication_controller import CommunicationController
from controllers.mail_controller import MailController
from controllers.admin_controller import AdminController
from views import game_view


class CommandController:
    def __init__(self, world, sessions, notifications):
        self.world, self.sessions = world, sessions
        self.rooms = RoomController(world, sessions, notifications)
        self.items = ItemController(world, self.rooms)
        self.communication = CommunicationController(world.config, sessions, notifications)
        self.mail = MailController(world, notifications)
        self.admin = AdminController(world, sessions, self.rooms)

    def allowed(self, session, permission):
        if permission == "P":
            return True
        if not session.playing:
            return False
        if permission == "A":
            return session.admin()
        return permission == "G" or session.user_id is not None

    def help(self, session, args):
        topic = args.pop(True); args.end()
        if topic and topic.lstrip('/').lower() == "tutorial":
            return game_view.tutorial()
        entries = COMMANDS
        if topic:
            entry = REGISTRY.get(topic.lstrip('/').lower())
            require(entry is not None, "Unknown help topic.")
            entries = (entry,)
        return self.help_lines(session, entries, bool(topic))

    def help_lines(self, session, entries, detailed):
        yield "PICO MUD commands (G guest, U user, O owner/admin, A admin):\n"
        for entry in entries:
            if self.allowed(session, entry[2]):
                yield from game_view.help_entry(entry, detailed)
        yield 'Quote multiword targets. Plain text or leading " speaks; leading : emotes.\n\n'

    def dispatch(self, session, line):
        if not line.startswith('/'):
            require(session.playing, "Use /connect <name> [password] or /connect guest.")
            if line.startswith(':'):
                return self.communication.handle(session, "emote", Arguments(line[1:]))
            return self.communication.handle(session, "say", Arguments(line[1:] if line.startswith('"') else line))
        args = Arguments(line[1:])
        word = args.pop().lower()
        entry = REGISTRY.get(word)
        if entry is None:
            require(session.playing, "Log in first.")
            try:
                return self.items.use(session, word, args)
            except GameError as error:
                raise GameError("Unknown command or unavailable action. Use /help. " + str(error))
        verb, _, permission, _, _ = entry
        require(self.allowed(session, permission), "Permission denied; use /help.")
        if verb == "help":
            return self.help(session, args)
        if verb == "quit":
            args.end(); self.sessions.kick(session, "Goodbye!\n"); return None
        if verb == "connect":
            require(not session.playing, "Disconnect before changing identity.")
            name = args.pop()
            if name.lower() == "guest":
                args.end(); self.sessions.enter(session, name)
            elif args.remaining():
                self.sessions.enter(session, name, args.rest())
            else:
                session.pending_name = name
                return None
            return self.welcome(session)
        require(session.playing, "Log in first.")
        if verb == "password":
            old, new = args.pop(), args.pop(); args.end()
            require(self.world.users.authenticate(session.name(), old) is not None, "Old password incorrect.")
            self.world.users.set_password(session.user_id, new)
            return "Password changed.\n"
        if verb in ("look", "examine", "exits", "rooms", "items", "who", "whoami"):
            return self.rooms.inspect(session, verb, args)
        if verb in DIRECTIONS or verb in ("go", "teleport", "home", "join"):
            return self.rooms.travel(session, verb, args)
        if verb in ("dig", "undig", "rename", "describe", "private", "sethome", "message", "lock", "unlock"):
            return self.rooms.build(session, verb, args)
        if verb == "destroy" and args.remaining().lower().startswith("room "):
            return self.rooms.build(session, verb, args)
        if verb in ("create", "destroy", "move", "interaction", "creature", "habbit"):
            return self.items.edit(session, verb, args)
        if verb in ("use", "interactions", "habbits"):
            return self.items.use(session, verb, args)
        if verb in ("say", "emote", "whisper", "page", "shout"):
            return self.communication.handle(session, verb, args)
        if verb == "mail":
            return self.mail.handle(session, args)
        return self.admin.handle(session, verb, args)

    def welcome(self, session):
        yield self.world.config.WELCOME_TEXT.rstrip('\n') + "\n"
        yield "Use /look, /go north or /n; /teleport to <id>; /teleport global home returns to room 1.\n"
        yield "Use /help tutorial for a guided introduction.\n"
        if session.user_id:
            yield "Use /home for your personal room, /help for commands.\n"
        yield from self.rooms.view(session)
