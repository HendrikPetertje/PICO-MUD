from models.storage import require, GameError
from modules.command_parser import identity, toggle
from views import game_view


class ItemController:
    def __init__(self, world, rooms):
        self.world, self.rooms = world, rooms

    def edit(self, session, verb, args):
        self.rooms.editable(session)
        if verb == "item":
            require(args.pop().lower() == "set", "Use /item set <item> visible ...")
            item = args.pop(); require(args.pop().lower() == "visible", "Expected visible.")
            operation = args.pop().lower()
            if operation == "clear":
                args.end(); self.world.items.rules(session.room_id, item, "visible_if", operation)
            else:
                rule = [args.pop(), args.pop().lower(), self.value(args)]
                args.end(); self.world.items.rules(session.room_id, item, "visible_if", operation, rule)
            return "Updated.\n"
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
            elif operation in ("set", "clear"):
                cron_id = identity(args.pop())
                if operation == "clear":
                    args.end(); self.world.items.property_effect(session.room_id, item, "set_variable", cron_id=cron_id)
                else:
                    value = [args.pop(), self.value(args)]; args.end()
                    self.world.items.property_effect(session.room_id, item, "set_variable", value, cron_id=cron_id)
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
        elif verb == "interaction":
            operation, item, action = args.pop().lower(), args.pop(), args.pop()
            if operation == "require":
                rule_operation = args.pop().lower()
                if rule_operation == "clear":
                    args.end(); self.world.items.rules(session.room_id, item, "available_if", rule_operation, action_name=action)
                else:
                    rule = [args.pop(), args.pop().lower(), self.value(args)]
                    args.end(); self.world.items.rules(session.room_id, item, "available_if", rule_operation, rule, action)
                return "Updated.\n"
            elif operation == "set":
                value = [args.pop(), self.value(args)]; args.end()
                self.world.items.property_effect(session.room_id, item, "set_variable", value, action_name=action)
                return "Updated.\n"
            elif operation == "clear":
                args.end(); self.world.items.property_effect(session.room_id, item, "set_variable", action_name=action)
                return "Updated.\n"
            elif operation == "add":
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

    def value(self, args):
        value = args.pop()
        return value if args.quoted or not value.lstrip("-").isdigit() else int(value)

    def actions(self, session, item):
        detailed = session.can_edit(self.world.rooms.get(session.room_id))
        owner = self.world.rooms.get(session.room_id)["owner_id"]
        actions = [action for action in item["interactions"] if
                   session.properties.allowed(session, owner, action["available_if"])]
        if not actions:
            yield "No interactions.\n"
        for action in actions:
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
        owner = self.world.rooms.get(session.room_id)["owner_id"]
        require(session.properties.allowed(session, owner, item["visible_if"]), "No such item.")
        if verb == "habbits":
            return self.habbits(session, item)
        actions = [action for action in item["interactions"] if session.properties.allowed(session, owner, action["available_if"])]
        if verb == "interactions" or (verb == "use" and len(actions) != 1):
            return self.actions(session, item)
        action = actions[0] if verb == "use" else next((entry for entry in actions if entry["action"] == verb), None)
        require(action is not None, "No such action.")
        if "set_variable" in action:
            key, value, changed = session.properties.apply(session, owner, action["set_variable"])
            return self.with_property(session, key, value, changed, action)
        flavor = action["flavor_text"]
        destination = action.get("teleport_to_room_id")
        if destination is None:
            return flavor + "\n"
        try:
            self.rooms.move(session, destination)
        except GameError as error:
            return flavor + "\n" + str(error) + "\n"
        return self.rooms.with_text(flavor, self.rooms.view(session))

    def with_property(self, session, key, value, changed, action):
        from models.properties import display_name
        message = action["flavor_text"] + "\n\n" + game_view.property_change(display_name(key), value, changed) + "\n"
        destination = action.get("teleport_to_room_id")
        if destination is None:
            return message
        try:
            self.rooms.move(session, destination)
        except GameError as error:
            return message + str(error) + "\n"
        return self.rooms.with_text(message.rstrip("\n"), self.rooms.view(session))
