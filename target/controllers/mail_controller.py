from models.storage import require
from modules.command_parser import Arguments, identity
from views import game_view


class MailController:
    def __init__(self, world, notifications):
        self.world, self.notifications = world, notifications

    def listing(self, user_id):
        snapshot = [(m["from_user_id"], m["title"]) for m in self.world.mail.inbox(user_id)]
        if not snapshot:
            yield "Your inbox is empty.\n"
        for number, (sender, title) in enumerate(snapshot, 1):
            if self.world.users.has(sender):
                yield game_view.mail_entry(number, self.world.users.get(sender)["name"], title)

    def handle(self, session, args):
        require(session.user_id is not None, "Guests cannot use mail.")
        operation = args.pop(True)
        if operation is None:
            return self.listing(session.user_id)
        operation = operation.lower()
        if operation in ("read", "delete"):
            number = identity(args.pop()); args.end()
            message = self.world.mail.read(session.user_id, number)
            if operation == "delete":
                self.world.mail.delete(session.user_id, number)
                return "Mail deleted.\n"
            return game_view.mail_message(self.world.users.get(message["from_user_id"])["name"], message)
        require(operation == "send", "Use mail, mail read, mail delete or mail send.")
        recipient = self.world.users.named(args.pop())
        start = args.position
        title_end = None
        while args.remaining():
            before = args.position
            value = args.pop()
            if value == "=" and not args.quoted:
                title_end = before
                break
        require(title_end is not None, "Use /mail send <user> <title> = <message>.")
        title = Arguments(args.source[start:title_end].strip()).rest()
        message = args.rest()
        self.world.mail.send(session.user_id, recipient["user_id"], title, message)
        self.notifications.user(recipient["user_id"], "New mail from " + session.name() + ".")
        return "Mail sent.\n"
