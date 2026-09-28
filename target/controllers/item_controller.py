from models.storage import require, GameError
from modules.command_parser import identity
from views import game_view


class ItemController:
    def __init__(self, world, rooms):
        self.world, self.rooms = world, rooms

    def edit(self, session, verb, args):
        self.rooms.editable(session)
        if verb == "create":
            return "Created item " + str(self.world.items.create(session.room_id, args.rest())) + ".\n"
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

    def use(self, session, verb, args):
        item = self.world.items.get(session.room_id, args.pop()); args.end()
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
