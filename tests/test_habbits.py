import gc
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "target"))

import config
from controllers.habbit_controller import HabbitController
from controllers.item_controller import ItemController
from controllers.room_controller import RoomController
from main import validate
from models.items import Items
from models.rooms import Rooms
from models.storage import GameError
from modules.commands import REGISTRY
from modules.command_parser import Arguments


if not hasattr(gc, "mem_free"):
    gc.mem_free = lambda: 1


class TestConfig:
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


class Viewer:
    room_id = 1

    def can_enter(self, room):
        return True


class Editor:
    room_id = 1

    def can_edit(self, room):
        return True


class HabbitsTest(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.rooms = Rooms(self.directory.name + "/rooms.json", TestConfig)
        self.rooms.data = [{"room_id": 1, "owner_id": 1, "name": "Home", "description": "",
                            "private": False, "exits": {}, "items": []}]
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
        self.assertEqual(REGISTRY["habbit"][2], "O")
        self.assertEqual(REGISTRY["habbits"][2], "G")
        valid = type("Config", (), {name: getattr(config, name) for name in dir(config) if name.isupper()})
        validate(valid)
        valid.MAX_CRON_JOBS_PER_ITEM = 0
        with self.assertRaises(ValueError):
            validate(valid)

    def test_room_view_separates_creatures(self):
        self.items.create(1, "sign")
        owl = self.items.create(1, "owl")
        self.items.creature(1, owl, True)
        world = type("World", (), {"items": self.items, "rooms": self.rooms})()
        lines = "".join(RoomController(world, Sessions([]), Notifications()).view(Viewer()))
        self.assertIn("Items:\n  sign [1]\n", lines)
        self.assertIn("Creatures:\n  owl [2]\n", lines)

    def test_habbit_command_forms_and_listing(self):
        item_id = self.items.create(1, "owl")
        world = type("World", (), {"items": self.items, "rooms": self.rooms})()
        rooms = type("RoomEditing", (), {"editable": lambda _, session: self.rooms.get(session.room_id)})()
        controller = ItemController(world, rooms)
        editor = Editor()
        controller.edit(editor, "habbit", Arguments("add owl 2 hoot"))
        controller.edit(editor, "habbit", Arguments("edit owl 1 chat on Who goes there?"))
        controller.edit(editor, "habbit", Arguments("edit owl 1 emote on ruffles feathers"))
        controller.edit(editor, "habbit", Arguments("edit owl 1 interval 3"))
        controller.edit(editor, "habbit", Arguments("edit owl 1 name evening hoot"))
        listed = "".join(controller.use(editor, "habbits", Arguments("owl")))
        self.assertIn("1: evening hoot every 3s", listed)
        self.assertIn("emote: ruffles feathers", listed)
        self.assertIn("chat_out: Who goes there?", listed)
        controller.edit(editor, "habbit", Arguments("edit owl 1 chat off"))
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
        scheduler = HabbitController(world, sessions, notifications)
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


if __name__ == "__main__":
    unittest.main()
