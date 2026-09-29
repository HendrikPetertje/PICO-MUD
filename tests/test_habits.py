import gc
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "target"))

import config
from controllers.habit_controller import HabitController
from controllers.item_controller import ItemController
from controllers.room_controller import RoomController
from controllers.command_controller import CommandController
from controllers.mail_controller import MailController
from main import validate
from models.items import Items
from models.properties import Properties, display_name
from models.properties import conditions, effect
from models import migrations
from models.rooms import Rooms
from models.storage import GameError
from modules.commands import REGISTRY
from modules.command_parser import Arguments
from views import game_view


if not hasattr(gc, "mem_free"):
    gc.mem_free = lambda: 1


class TestConfig:
    MAX_ROOMS_PER_USER = 10
    MAX_ITEMS_PER_ROOM = 5
    MAX_INTERACTIONS_PER_ITEM = 2
    MAX_CRON_JOBS_PER_ITEM = 3
    MAX_NAME_LENGTH = 60
    MAX_DESCRIPTION_LENGTH = 600
    MAX_TEXT_LENGTH = 250
    MIN_FREE_MEMORY = 0


class Users:
    data = [{"user_id": 1}]

    def has(self, identity):
        return identity == 1


class Sessions:
    def __init__(self, room_ids):
        self.room_ids = room_ids

    def live(self):
        return [type("Session", (), {"room_id": room_id})() for room_id in self.room_ids]


class Notifications:
    def __init__(self):
        self.messages = []

    def room(self, room_id, message):
        self.messages.append((room_id, message))

    def send(self, session, message):
        self.messages.append((session.room_id, message))


class Viewer:
    room_id = 1
    user_id = None
    properties = Properties()

    def can_enter(self, room):
        return True

    def admin(self):
        return False


class Editor:
    room_id = 1
    user_id = 1
    properties = Properties()

    def can_edit(self, room):
        return True

    def admin(self):
        return False


class Player(Editor):
    def __init__(self, user_id, room_id=1, admin=False):
        self.user_id = user_id
        self.room_id = room_id
        self._admin = admin
        self.properties = Properties()

    def admin(self):
        return self._admin

    def can_enter(self, room):
        return self.properties.allowed(self, room["owner_id"], room["unlocked_if"])


class HabitsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.rooms = Rooms(self.directory.name + "/rooms.json", TestConfig)
        self.rooms.data = [{"room_id": 1, "owner_id": 1, "name": "Home", "description": "",
                             "private": False, "unlocked_if": [], "exits": {}, "items": []}]
        self.items = Items(self.rooms, TestConfig, set())

    def tearDown(self):
        self.directory.cleanup()

    def test_creature_and_cron_lifecycle(self):
        item_id = self.items.create(1, "owl")
        self.items.creature(1, item_id, True)
        self.items.cron(1, item_id, "add", field="hoot", value=2)
        item = self.items.get(1, item_id)
        self.assertTrue(item["creature"])
        self.assertEqual(item["cron_jobs"][0]["name"], "hoot")
        self.items.cron(1, item_id, "edit", 1, "emote", "ruffles feathers")
        self.items.cron(1, item_id, "edit", 1, "chat_out", "Who goes there?")
        self.items.validate()
        self.assertEqual(len(self.items.crons(self.items.get(1, item_id))), 1)

    def test_commands_and_configuration_are_registered(self):
        self.assertEqual(REGISTRY["creature"][2], "O")
        self.assertEqual(REGISTRY["habit"][2], "O")
        self.assertEqual(REGISTRY["habits"][2], "G")
        valid = type("Config", (), {name: getattr(config, name) for name in dir(config) if name.isupper()})
        validate(valid)
        valid.MAX_CRON_JOBS_PER_ITEM = 0
        with self.assertRaises(ValueError):
            validate(valid)

    def test_help_lists_focused_topics_before_commands(self):
        self.assertEqual("".join(game_view.help_topics()),
                         "PICO MUD help\n\n"
                         "Choose a topic:\n"
                         "  /help tutorial - Find your feet: looking around, moving, and chatting.\n"
                         "  /help user - Meet people, manage your account, and send messages.\n"
                         "  /help movement - Travel by exits, teleport, visit homes, and join players.\n"
                         "  /help building - Shape rooms, exits, descriptions, and scenery.\n"
                          "  /help programming - Give items and creatures actions, habits, and variables.\n")
        programming = "".join(game_view.help_topic("programming"))
        self.assertIn("Variables remember small things", programming)
        self.assertIn('values that look like numbers, such as "01"', programming)
        self.assertIn("/interaction require <item> <action> add|remove", programming)
        self.assertNotIn("/help admin", "".join(game_view.help_topics()))
        self.assertIn("/help admin - Manage players, the world, and server operations. [A]",
                      "".join(game_view.help_topics(True)))

    def test_focused_help_topics_show_introductions_and_commands(self):
        controller = CommandController.__new__(CommandController)
        guest = type("Guest", (), {"playing": True, "user_id": None, "admin": lambda _: False})()
        expected = {
            "tutorial": ("Getting started", "/connect <name> [password] | guest", "  Aliases: Login"),
            "user": ("Users and players", "/who", "/look [at <item|direction|player>]"),
            "movement": ("Movement", "/go <direction>", "/teleport [to] home | [to] global home | to <room_id>"),
            "programming": ("Programming rooms", "/interactions <item>", "/habits <item>"),
        }
        for topic, values in expected.items():
            lines = "".join(controller.help(guest, Arguments(topic)))
            for value in values:
                self.assertIn(value, lines)
            self.assertIn("\n  ", lines)
            self.assertNotIn("/password <old> <new>", lines)
            self.assertNotIn("/dig", lines)
        building = "".join(controller.help(guest, Arguments("building")))
        self.assertIn("Building\n", building)
        self.assertIn("Commands:\n", building)
        self.assertNotIn("/create", building)
        owner = type("Owner", (), {"playing": True, "user_id": 1, "admin": lambda _: False})()
        building = "".join(controller.help(owner, Arguments("building")))
        self.assertIn("/create <item name>\n  Create an item in this room.\n\n", building)
        self.assertIn("/dig <dir> <room name> | <dir> to <room_id>\n", building)

    def test_admin_help_entry_has_weight_marker(self):
        entry = REGISTRY["save"]
        self.assertIn("/save [A]\n", "".join(game_view.help_entry(entry, True)))
        self.assertNotIn("[A]", "".join(game_view.help_entry(REGISTRY["look"], True)))

    def test_help_entry_formats_multiple_aliases(self):
        entry = ("test", "first second", "P", "", "Test command.")
        self.assertIn("  Aliases: First Second\n", "".join(game_view.help_entry(entry, True)))

    def test_admin_help_is_admin_only_and_marks_commands(self):
        controller = CommandController.__new__(CommandController)
        guest = type("Guest", (), {"playing": True, "user_id": None, "admin": lambda _: False})()
        with self.assertRaises(GameError):
            "".join(controller.help(guest, Arguments("admin")))
        admin = type("Admin", (), {"playing": True, "user_id": 1, "admin": lambda _: True})()
        lines = "".join(controller.help(admin, Arguments("admin")))
        self.assertIn("Administration\n", lines)
        self.assertIn("/user", lines)
        self.assertIn("/save [A]\n", lines)

    def test_room_view_separates_creatures(self):
        self.items.create(1, "sign")
        owl = self.items.create(1, "owl")
        self.items.creature(1, owl, True)
        world = type("World", (), {"items": self.items, "rooms": self.rooms,
                                    "users": type("Users", (), {"data": []})()})()
        lines = "".join(RoomController(world, Sessions([]), Notifications()).view(Viewer()))
        self.assertIn("Items:\n  sign [1]\n", lines)
        self.assertIn("Creatures:\n  owl [2]\n", lines)

    def test_room_view_hides_empty_sections(self):
        world = type("World", (), {"items": self.items, "rooms": self.rooms,
                                    "users": type("Users", (), {"data": []})()})()
        lines = "".join(RoomController(world, Sessions([]), Notifications()).view(Viewer()))
        self.assertNotIn("Exits:\n", lines)
        self.assertNotIn("Items:\n", lines)
        self.assertNotIn("Creatures:\n", lines)
        self.assertIn("Here: \n\n", lines)

    def test_item_view_hides_empty_actions(self):
        item_id = self.items.create(1, "sign")
        world = type("World", (), {"items": self.items, "rooms": self.rooms,
                                    "users": type("Users", (), {"data": []})()})()
        controller = RoomController(world, Sessions([]), Notifications())
        item = self.items.get(1, item_id)
        self.assertNotIn("Actions:\n", "".join(controller.item_view(Viewer(), item)))
        detailed = "".join(controller.item_view(Viewer(), item, True))
        self.assertIn("Item 1 in room 1, owner 1\n", detailed)
        self.assertNotIn("Actions:\n", detailed)
        self.items.interaction(1, item_id, "add", "read", "The sign is faded.")
        lines = "".join(controller.item_view(Viewer(), self.items.get(1, item_id)))
        self.assertIn("Actions:\n  read\n", lines)

    def test_owner_action_details_show_requirements_and_effects(self):
        item_id = self.items.create(1, "dish washer")
        self.items.interaction(1, item_id, "add", "put_cup", "You put the cup away.")
        self.items.rules(1, item_id, "available_if", "add", ["has_cup", "equals", "yes"], "put_cup")
        self.items.property_effect(1, item_id, "set_variable", ["has_cup", "no"], action_name="put_cup")
        world = type("World", (), {"items": self.items, "rooms": self.rooms,
                                     "users": type("Users", (), {"data": []})()})()
        lines = "".join(RoomController(world, Sessions([]), Notifications()).item_view(Editor(), self.items.get(1, item_id), True))
        self.assertIn("put_cup:\n    Description: You put the cup away.", lines)
        self.assertIn('Requirements:\n      - has_cup equals "yes"', lines)
        self.assertIn('Sets: has_cup "no"', lines)

    def test_owner_examine_includes_habit_details(self):
        item_id = self.items.create(1, "goblin")
        self.items.cron(1, item_id, "add", field="grumble", value=30)
        world = type("World", (), {"items": self.items, "rooms": self.rooms,
                                     "users": type("Users", (), {"data": []})()})()
        lines = "".join(RoomController(world, Sessions([]), Notifications()).item_view(
            Editor(), self.items.get(1, item_id), True))
        self.assertIn("Habits:\n  grumble (1):\n", lines)
        self.assertIn("    Interval: 30 seconds\n", lines)
        self.assertIn("    Chat: unset\n", lines)
        self.assertIn("    Emote: unset\n", lines)
        self.assertIn("    State: on\n", lines)

    def test_habit_command_forms_and_listing(self):
        item_id = self.items.create(1, "owl")
        world = type("World", (), {"items": self.items, "rooms": self.rooms})()
        rooms = type("RoomEditing", (), {"editable": lambda _, session: self.rooms.get(session.room_id)})()
        controller = ItemController(world, rooms)
        editor = Editor()
        controller.edit(editor, "habit", Arguments("add owl 2 hoot"))
        controller.edit(editor, "habit", Arguments("edit owl 1 chat on Who goes there?"))
        controller.edit(editor, "habit", Arguments("edit owl 1 emote on ruffles feathers"))
        controller.edit(editor, "habit", Arguments("edit owl 1 interval 3"))
        controller.edit(editor, "habit", Arguments("edit owl 1 name evening hoot"))
        listed = "".join(controller.use(editor, "habits", Arguments("owl")))
        self.assertIn("evening hoot (1):", listed)
        self.assertIn("Interval: 3 seconds", listed)
        self.assertIn("Emote: ruffles feathers", listed)
        self.assertIn("Chat: Who goes there?", listed)
        self.assertIn("State: on", listed)
        controller.edit(editor, "habit", Arguments("edit owl 1 chat off"))
        self.assertNotIn("chat_out", self.items.get(1, item_id)["cron_jobs"][0])

    def test_cron_validation_preserves_item(self):
        item_id = self.items.create(1, "bell")
        for number in range(3):
            self.items.cron(1, item_id, "add", field="job" + str(number), value=1)
        before = self.items.get(1, item_id).copy()
        with self.assertRaises(GameError):
            self.items.cron(1, item_id, "add", field="extra", value=1)
        self.assertEqual(self.items.get(1, item_id), before)
        with self.assertRaises(GameError):
            self.items.cron(1, item_id, "edit", 1, "interval_seconds", 0)
        self.assertEqual(self.items.get(1, item_id), before)
        with self.assertRaises(GameError):
            self.items.cron(1, item_id, "edit", 4, "name", "missing")
        self.assertEqual(self.items.get(1, item_id), before)
        with self.assertRaises(GameError):
            self.items.cron(1, item_id, "edit", 1, "name", "x" * 61)
        self.assertEqual(self.items.get(1, item_id), before)

    def test_cron_data_round_trips_and_invalid_data_fails(self):
        item_id = self.items.create(1, "owl")
        self.items.creature(1, item_id, True)
        self.items.cron(1, item_id, "add", field="hoot", value=2)
        self.items.cron(1, item_id, "edit", 1, "chat_out", "Who goes there?")
        self.rooms.save_if_dirty()
        loaded = Rooms(self.directory.name + "/rooms.json", TestConfig)
        loaded.load()
        Items(loaded, TestConfig, set()).validate()
        self.assertTrue(loaded.get(1)["items"][0]["creature"])
        self.assertEqual(loaded.get(1)["items"][0]["cron_jobs"][0]["chat_out"], "Who goes there?")
        loaded.get(1)["items"][0]["cron_jobs"][0]["interval_seconds"] = 0
        with self.assertRaises(GameError):
            Items(loaded, TestConfig, set()).validate()

    def test_move_preserves_creature_cron_and_interaction_data(self):
        self.rooms.data.append({"room_id": 2, "owner_id": 1, "name": "Other", "description": "",
                                "private": False, "exits": {}, "items": []})
        item_id = self.items.create(1, "owl")
        self.items.creature(1, item_id, True)
        self.items.interaction(1, item_id, "add", "pet", "The owl accepts the attention.")
        self.items.cron(1, item_id, "add", field="hoot", value=2)
        moved_id = self.items.move(1, item_id, 2)
        moved = self.items.get(2, moved_id)
        self.assertTrue(moved["creature"])
        self.assertEqual(moved["interactions"][0]["action"], "pet")
        self.assertEqual(moved["cron_jobs"][0]["name"], "hoot")

    def test_scheduler_requires_occupancy_and_orders_output(self):
        item_id = self.items.create(1, "owl")
        self.items.cron(1, item_id, "add", field="hoot", value=1)
        self.items.cron(1, item_id, "edit", 1, "emote", "ruffles feathers")
        self.items.cron(1, item_id, "edit", 1, "chat_out", "Who goes there?")
        world = type("World", (), {"rooms": self.rooms})()
        sessions, notifications = Sessions([]), Notifications()
        scheduler = HabitController(world, sessions, notifications)
        scheduler.tick(1000)
        self.assertEqual(notifications.messages, [])
        sessions.room_ids = [1]
        scheduler.tick(999)
        self.assertEqual(notifications.messages, [])
        scheduler.tick(1)
        self.assertEqual(notifications.messages, [
            (1, "owl ruffles feathers"),
            (1, 'owl says: "Who goes there?"'),
        ])
        self.items.destroy(1, item_id)
        scheduler.tick(1000)
        self.assertEqual(scheduler.elapsed, {})

    def test_properties_are_scoped_bounded_and_clamped(self):
        properties = Properties()
        player = type("Player", (), {"user_id": 2, "admin": lambda _: False})()
        self.assertFalse(properties.allowed(player, 1, [["key", "equals", 1]]))
        self.assertEqual(properties.apply(player, 1, ["health", 99]), ("health", 99, True))
        self.assertEqual(properties.apply(player, 1, ["health", 5]), ("health", 100, True))
        self.assertTrue(properties.allowed(player, 1, [["health", "more_than", 20]]))
        for number in range(5):
            properties.apply(player, 1, ["v_" + str(number), "x"])
        with self.assertRaises(GameError):
            properties.apply(player, 1, ["too_many", "x"])
        self.assertEqual(properties.apply(player, 3, ["other", "x"]), ("other", "x", True))
        with self.assertRaises(GameError):
            conditions([["key", "invalid", 1]])
        with self.assertRaises(GameError):
            effect(["key", 101])

    def test_properties_require_identifier_names(self):
        for name in ("has blue key", "Has_key", "has__key", "has_key_", "1_key"):
            with self.assertRaises(GameError):
                effect([name, "yes"])
        self.assertEqual(effect(["has_blue_key", "01"]), ["has_blue_key", "01"])
        self.assertEqual(display_name("has_blue_key"), "Has blue key")

    def test_room_schema_migration_is_idempotent(self):
        self.rooms.data[0]["items"] = [{"id": 1, "name": "Box", "description": "",
                                         "interactions": [{"action": "open", "flavor_text": "Click."}]}]
        self.assertTrue(migrations.apply(self.rooms))
        room = self.rooms.get(1)
        self.assertEqual(room["unlocked_if"], [])
        self.assertEqual(room["items"][0]["visible_if"], [])
        self.assertEqual(room["items"][0]["interactions"][0]["available_if"], [])
        self.rooms.dirty = False
        self.assertFalse(migrations.apply(self.rooms))
        self.assertFalse(self.rooms.dirty)

    def test_nested_property_metadata_validation_preserves_records(self):
        item_id = self.items.create(1, "box")
        self.items.interaction(1, item_id, "add", "open", "Click.")
        self.items.rules(1, item_id, "visible_if", "add", ["has_key", "equals", "yes"])
        self.items.rules(1, item_id, "available_if", "add", ["has_key", "equals", "yes"], "open")
        self.items.property_effect(1, item_id, "set_variable", ["opened", 1], action_name="open")
        self.items.cron(1, item_id, "add", field="reset", value=1)
        self.items.property_effect(1, item_id, "set_variable", ["opened", -1], cron_id=1)
        self.items.validate()
        before = self.items.get(1, item_id).copy()
        with self.assertRaises(GameError):
            self.items.rules(1, item_id, "visible_if", "add", ["bad name", "equals", 1])
        self.assertEqual(self.items.get(1, item_id), before)

    def test_builder_commands_preserve_quoted_numeric_strings(self):
        self.rooms.data.append({"room_id": 2, "owner_id": 1, "name": "Vault", "description": "",
                                "private": False, "unlocked_if": [], "exits": {}, "items": []})
        item_id = self.items.create(1, "chest")
        self.items.interaction(1, item_id, "add", "open", "Click.")
        world = type("World", (), {"items": self.items, "rooms": self.rooms,
                                    "users": type("Users", (), {"data": []})()})()
        editor = Player(1)
        rooms = RoomController(world, Sessions([]), Notifications())
        controller = ItemController(world, rooms)
        rooms.build(type("Editor", (), {"room_id": 2, "can_edit": lambda _, room: True})(),
                    "room-unlock-rules", Arguments("add has_key equals \"01\""))
        controller.edit(editor, "item", Arguments("set chest visible add has_key equals \"01\""))
        controller.edit(editor, "interaction", Arguments("require chest open add has_key equals \"01\""))
        controller.edit(editor, "interaction", Arguments("set chest open opened 1"))
        self.assertEqual(self.rooms.get(2)["unlocked_if"], [["has_key", "equals", "01"]])
        item = self.items.get(1, item_id)
        self.assertEqual(item["visible_if"], [["has_key", "equals", "01"]])
        self.assertEqual(item["interactions"][0]["available_if"], [["has_key", "equals", "01"]])
        self.assertEqual(item["interactions"][0]["set_variable"], ["opened", 1])

    def test_arguments_accept_smart_quotes_and_preserve_ascii_escapes(self):
        args = Arguments('“coffee machine” “01”')
        self.assertEqual(args.pop(), "coffee machine")
        self.assertTrue(args.quoted)
        self.assertEqual(args.pop(), "01")
        self.assertTrue(args.quoted)
        self.assertEqual(Arguments('"coffee \\"machine\\""').pop(), 'coffee "machine"')
        for source in ('“coffee machine', '“coffee machine"'):
            with self.assertRaises(GameError):
                Arguments(source).pop()
        with self.assertRaises(GameError):
            Arguments('coffee“machine”').pop()

    def test_smart_quotes_work_for_item_actions_speech_and_mail_titles(self):
        item_id = self.items.create(1, "coffee machine")
        self.items.interaction(1, item_id, "add", "push", "Coffee is ready.")
        world = type("World", (), {"items": self.items, "rooms": self.rooms})()
        player = Player(2)
        controller = ItemController(world, RoomController(world, Sessions([]), Notifications()))
        self.assertEqual(controller.use(player, "push", Arguments('“coffee machine”')), "Coffee is ready.\n")
        self.assertEqual(controller.use(player, "push", Arguments('"coffee machine"')), "Coffee is ready.\n")

        received = []
        command = CommandController.__new__(CommandController)
        command.communication = type("Communication", (), {
            "handle": lambda _, session, verb, args: received.append((verb, args.rest()))
        })()
        session = type("Session", (), {"playing": True})()
        command.dispatch(session, "hello")
        command.dispatch(session, "“hello")
        command.dispatch(session, ":waves")
        self.assertEqual(received, [("say", "hello"), ("say", "hello"), ("emote", "waves")])

        sent = []
        mail = MailController(
            type("World", (), {
                "users": type("Users", (), {"named": lambda _, name: {"user_id": 2}})(),
                "mail": type("Mail", (), {"send": lambda _, *values: sent.append(values)})(),
            })(),
            type("Notifications", (), {"user": lambda *_: None})(),
        )
        mail.handle(type("Session", (), {"user_id": 1, "name": lambda _: "sender"})(),
                    Arguments('send recipient “coffee title” = hello'))
        self.assertEqual(sent, [(1, 2, "coffee title", "hello")])

    def test_conditions_hide_content_and_owner_bypasses(self):
        item_id = self.items.create(1, "treasure")
        self.items.interaction(1, item_id, "add", "open", "Gold.")
        self.items.rules(1, item_id, "visible_if", "add", ["has_key", "equals", "yes"])
        visitor, owner, admin = Player(2), Player(1), Player(3, admin=True)
        item = self.items.get(1, item_id)
        self.assertFalse(visitor.properties.allowed(visitor, 1, item["visible_if"]))
        self.assertTrue(owner.properties.allowed(owner, 1, item["visible_if"]))
        self.assertTrue(admin.properties.allowed(admin, 1, item["visible_if"]))
        visitor.properties.apply(visitor, 1, ["has_key", "yes"])
        self.assertTrue(visitor.properties.allowed(visitor, 1, item["visible_if"]))

    def test_hidden_action_does_not_resolve_by_verb(self):
        item_id = self.items.create(1, "lever")
        self.items.interaction(1, item_id, "add", "pull", "Click.")
        self.items.rules(1, item_id, "available_if", "add", ["has_key", "equals", "yes"], "pull")
        world = type("World", (), {"items": self.items, "rooms": self.rooms})()
        controller = ItemController(world, RoomController(world, Sessions([]), Notifications()))
        visitor = Player(2)
        with self.assertRaises(GameError):
            controller.use(visitor, "pull", Arguments("lever"))

    def test_room_condition_blocks_nonowner_and_allows_owner(self):
        self.rooms.data.append({"room_id": 2, "owner_id": 1, "name": "Vault", "description": "",
                                "private": False, "unlocked_if": [], "exits": {}, "items": []})
        self.rooms.unlock_rules(2, "add", ["has_key", "equals", "yes"])
        visitor, owner = Player(2), Player(1)
        self.assertFalse(visitor.can_enter(self.rooms.get(2)))
        self.assertTrue(owner.can_enter(self.rooms.get(2)))
        visitor.properties.apply(visitor, 1, ["has_key", "yes"])
        self.assertTrue(visitor.can_enter(self.rooms.get(2)))

    def test_global_home_rejects_unlock_rules(self):
        with self.assertRaises(GameError):
            self.rooms.unlock_rules(1, "add", ["has_key", "equals", "yes"])

    def test_personal_home_rejects_unlock_rules_and_privacy(self):
        self.rooms.data.append({"room_id": 2, "owner_id": 1, "name": "Home", "description": "",
                                "private": False, "unlocked_if": [], "exits": {}, "items": []})
        users = type("Users", (), {"data": [{"user_id": 1, "home_room_id": 2}], "has": lambda _, value: value == 1})()
        self.rooms.validate(users)
        self.rooms.get(2)["private"] = True
        with self.assertRaises(GameError):
            self.rooms.validate(users)
        self.rooms.get(2)["private"] = False
        self.rooms.get(2)["unlocked_if"] = [["has_key", "equals", "yes"]]
        with self.assertRaises(GameError):
            self.rooms.validate(users)

    def test_visibility_rules_and_interaction_effect(self):
        item_id = self.items.create(1, "chest")
        self.items.interaction(1, item_id, "add", "open", "Click.")
        self.items.rules(1, item_id, "visible_if", "add", ["has_key", "equals", "yes"])
        self.items.rules(1, item_id, "available_if", "add", ["has_key", "equals", "yes"], "open")
        self.items.property_effect(1, item_id, "set_variable", ["has_key", "yes"], action_name="open")
        visitor = Viewer()
        self.assertFalse(visitor.properties.allowed(visitor, 1, self.items.get(1, item_id)["visible_if"]))
        visitor.properties.apply(visitor, 1, ["has_key", "yes"])
        self.assertTrue(visitor.properties.allowed(visitor, 1, self.items.get(1, item_id)["visible_if"]))
        self.assertTrue(visitor.properties.allowed(visitor, 1, self.items.get(1, item_id)["interactions"][0]["available_if"]))

    def test_interaction_property_change_has_a_labeled_block(self):
        item_id = self.items.create(1, "coffee machine")
        self.items.interaction(1, item_id, "add", "push", "Coffee is ready.")
        self.items.property_effect(1, item_id, "set_variable", ["has_cup", "yes"], action_name="push")
        world = type("World", (), {"items": self.items, "rooms": self.rooms})()
        controller = ItemController(world, RoomController(world, Sessions([]), Notifications()))
        player = Player(2)
        self.assertEqual(controller.use(player, "push", Arguments('"coffee machine"')),
                         "Coffee is ready.\n\nChanges to you:\n  Has cup: yes\n")
        self.assertEqual(controller.use(player, "push", Arguments('"coffee machine"')),
                         "Coffee is ready.\n\nChanges to you:\n  Has cup: yes - remains unchanged\n")

    def test_cron_effect_updates_each_occupant_and_silences_unchanged_values(self):
        item_id = self.items.create(1, "bard")
        self.items.cron(1, item_id, "add", field="sing", value=1)
        self.items.property_effect(1, item_id, "set_variable", ["bard_mood", "calm"], cron_id=1)
        players = []
        for number in range(2):
            player = type("Player", (), {"room_id": 1, "user_id": number + 2,
                                           "properties": Properties(), "admin": lambda _: False})()
            players.append(player)
        sessions = type("Sessions", (), {"live": lambda _: players})()
        notifications = Notifications()
        HabitController(type("World", (), {"rooms": self.rooms})(), sessions, notifications).tick(1000)
        self.assertEqual([p.properties.values(p) for p in players], [[(1, "bard_mood", "calm")], [(1, "bard_mood", "calm")]])
        notifications.messages = []
        HabitController(type("World", (), {"rooms": self.rooms})(), sessions, notifications).tick(1000)
        self.assertEqual(notifications.messages, [])


if __name__ == "__main__":
    unittest.main()
