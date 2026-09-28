from models.storage import require, GameError
from modules.command_parser import identity, toggle
from views import game_view


class ItemController:
    def __init__(self, world, rooms):
        self.world, self.rooms = world, rooms

    def edit(self, session, verb, args):
        self.rooms.editable(session)
        if verb == "create":
            return "Created item " + str(self.world.items.create(session.room_id, args.rest())) + ".\n"
        if verb == "creature":
            item = args.pop()
            value = toggle(args.pop(True), bool(self.world.items.get(session.room_id, item).get("creature")))
            args.end()
            self.world.items.creature(session.room_id, item, value)
            return "Updated.\n"
        if verb == "destroy":
            item = args.pop(); args.end()
            self.world.items.destroy(session.room_id, item)
        elif verb == "move":
            item = args.pop()
            require(args.pop().lower() == "to", "Use /move <item> to <room_id>.")
            target = identity(args.pop()); args.end()
            self.rooms.editable(session, target)
            new_id = self.world.items.move(session.room_id, item, target)
            return "Moved item; new id " + str(new_id) + ".\n"
        elif verb == "habbit":
            operation, item = args.pop().lower(), args.pop()
            if operation == "add":
                interval = identity(args.pop())
                self.world.items.cron(session.room_id, item, "add", field=args.rest(), value=interval)
            else:
                cron_id = identity(args.pop())
                if operation == "remove":
                    args.end()
                    self.world.items.cron(session.room_id, item, "remove", cron_id)
                else:
                    require(operation == "edit", "Use habbit add, edit or remove.")
                    field = args.pop().lower()
                    if field == "interval":
                        value = identity(args.pop()); args.end(); field = "interval_seconds"
                    elif field == "name":
                        value = args.rest()
                    else:
                        require(field in ("chat", "emote"), "Edit interval, name, chat or emote.")
                        enabled = args.pop().lower()
                        require(enabled in ("on", "off"), "Use on or off.")
                        value = args.rest() if enabled == "on" else None
                        if enabled == "off":
                            args.end()
                        field = "chat_out" if field == "chat" else field
                    self.world.items.cron(session.room_id, item, "edit", cron_id, field, value)
        else:
            operation, item, action = args.pop().lower(), args.pop(), args.pop()
            if operation == "add":
                value = args.rest()
            elif operation == "teleport":
                value = args.pop(); args.end()
                value = None if value.lower() == "none" else identity(value)
                if value is not None:
                    require(session.can_enter(self.world.rooms.get(value)), "Target room is private.")
            else:
                require(operation == "remove", "Use interaction add, teleport or remove.")
                args.end(); value = None
            self.world.items.interaction(session.room_id, item, operation, action, value)
        return "Updated.\n"

    def actions(self, session, item):
        detailed = session.can_edit(self.world.rooms.get(session.room_id))
        if not item["interactions"]:
            yield "No interactions.\n"
        for action in item["interactions"]:
            yield game_view.action_entry(action, detailed)

    def habbits(self, session, item):
        detailed = session.can_edit(self.world.rooms.get(session.room_id))
        jobs = self.world.items.crons(item)
        if not jobs:
            yield "No habbits.\n"
        for job in jobs:
            yield game_view.habbit_entry(job, detailed)

    def use(self, session, verb, args):
        item = self.world.items.get(session.room_id, args.pop()); args.end()
        if verb == "habbits":
            return self.habbits(session, item)
        if verb == "interactions" or (verb == "use" and len(item["interactions"]) != 1):
            return self.actions(session, item)
        action = item["interactions"][0] if verb == "use" else self.world.items.action(item, verb)
        flavor = action["flavor_text"]
        destination = action.get("teleport_to_room_id")
        if destination is None:
            return flavor + "\n"
        try:
            self.rooms.move(session, destination)
        except GameError as error:
            return flavor + "\n" + str(error) + "\n"
        return self.rooms.with_text(flavor, self.rooms.view(session))
