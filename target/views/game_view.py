"""Pure, bounded text renderers. Controllers supply visible records only."""


def chunks(lines, prompt=True):
    if isinstance(lines, str):
        lines = (lines,)
    for line in lines:
        room_id = None
        if type(line) is tuple:
            line, room_id = line
        # At most 128 code points / 512 UTF-8 bytes before CRLF expansion.
        for start in range(0, len(line), 128):
            chunk = line[start:start + 128]
            yield (chunk, room_id) if room_id is not None else chunk
    # Terminal chunk lets the controller release the response before the peer
    # sees the prompt and immediately submits its next command.
    yield ("> " if prompt else "", None)


def room_header(room):
    yield "\n" + room["name"] + " [" + str(room["room_id"]) + "]\n"
    yield room["description"] + "\n"


def exit_line(way, exit):
    return "  " + way + ": " + exit["name"] + (" [locked]" if exit["locked"] else "") + "\n"


def room_entry(room):
    return str(room["room_id"]) + ": " + room["name"] + (" [private]" if room["private"] else "") + "\n"


def item_entry(room_id, item):
    return "Room " + str(room_id) + ", item " + str(item["id"]) + ": " + item["name"] + "\n"


def room_item_line(item):
    return "  " + item["name"] + " [" + str(item["id"]) + "]\n"


def action_entry(action, detailed=False):
    result = "  " + action["action"]
    if detailed:
        result += ": " + action["flavor_text"]
        if "teleport_to_room_id" in action:
            result += " -> room " + str(action["teleport_to_room_id"])
    return result + "\n"


def habbit_entry(job, detailed=False):
    result = "{}: {} every {}s".format(job["id"], job["name"], job["interval_seconds"])
    if detailed:
        for field in ("emote", "chat_out"):
            if field in job:
                result += " {}: {}".format(field, job[field])
    return result + "\n"


def notification(message, prompt=True):
    return "\n" + message.rstrip("\n") + "\n" + ("> " if prompt else "")


def speech(name, message, emote=False):
    return name + (" " if emote else ' says: "') + message + ("" if emote else '"')


def property_change(name, value, changed=True):
    return "Changes to you:\n  {}: {}{}".format(
        name, value, "" if changed else " - remains unchanged")


def presence(name, event):
    return name + " " + event + "."


def private_message(sender, target, message, verb):
    return sender + " " + verb + " to " + target + ": " + message


def user_entry(user):
    return "{}: {} admin={} banned={} home={}\n".format(
        user["user_id"], user["name"], user["admin"], user["banned"], user["home_room_id"])


def mail_entry(number, sender, title):
    return "{}: {} — {}\n".format(number, sender, title)


def mail_message(sender, message):
    yield "From: " + sender + "\n"
    yield "Title: " + message["title"] + "\n"
    yield message["message"] + "\n"


def help_entry(entry, detailed=False):
    verb, aliases, permission, syntax, description = entry
    yield "/" + verb + (" " + syntax if syntax else "") + (" [A]" if permission == "A" else "") + "\n"
    if detailed:
        if aliases:
            yield "  Aliases: " + aliases.title() + "\n"
        yield "  " + description + "\n\n"


def help_topics(admin=False):
    yield "PICO MUD help\n\n"
    yield "Choose a topic:\n"
    yield "  /help tutorial - Find your feet: looking around, moving, and chatting.\n"
    yield "  /help user - Meet people, manage your account, and send messages.\n"
    yield "  /help movement - Travel by exits, teleport, visit homes, and join players.\n"
    yield "  /help building - Shape rooms, exits, descriptions, and scenery.\n"
    yield "  /help programming - Give items and creatures actions, habbits, and variables.\n"
    if admin:
        yield "  /help admin - Manage players, the world, and server operations. [A]\n"


def help_topic(topic):
    if topic == "tutorial":
        yield "Getting started\n\n"
        yield "Welcome to PICO MUD. Start by looking around, reading room descriptions, and trying a few commands. "
        yield "There is no rush; explore at your own pace and see what you find.\n\n"
        yield "Plain text speaks to everyone in the room, while a leading : lets you emote. "
        yield "When you want more detail, the other help topics are waiting for you.\n\n"
    elif topic == "user":
        yield "Users and players\n\n"
        yield "Guests are welcome to explore and join the conversation. Registered users also have passwords, homes, and mail, so they can settle into the world a little more deeply.\n\n"
        yield "Use these commands to see who is nearby, learn about other players, and keep in touch. "
        yield "Whispers stay in the room; pages can reach an online player anywhere.\n\n"
    elif topic == "movement":
        yield "Movement\n\n"
        yield "Every room is a place to pause, look around, and choose where to go next. "
        yield "Travel by cardinal or vertical exits, or take a more direct route when you know where you are headed.\n\n"
        yield "If a path refuses you, it may be locked, private, or waiting for the right condition. "
        yield "Global home is always there when you want a familiar place to return to.\n\n"
    elif topic == "building":
        yield "Building\n\n"
        yield "A good room gives people a reason to linger. Build in rooms you own, connect spaces together, and give each place a name and description that makes it feel lived in.\n\n"
        yield "Items are scenery, not inventory. Use them to add texture, secrets, and characters to your rooms; admins can help keep any property in good order.\n\n"
    elif topic == "programming":
        yield "Programming rooms\n\n"
        yield "Programming is how you give a place a little spark. Interactions let an item or creature respond to players; habbits let it do something on its own while people are nearby.\n\n"
        yield "Variables remember small things for one player's visit: a key they found, a door they opened, or a blessing they received. "
        yield "They belong to the owner whose world set them and disappear when the player leaves or the MUD restarts.\n\n"
        yield "Every rule in a condition list must pass. Numbers can rise or fall between 0 and 100, while strings replace a value. "
        yield "Quote strings, especially values that look like numbers, such as \"01\".\n\n"
    else:
        yield "Administration\n\n"
        yield "Administration helps keep the shared world welcoming and running smoothly. These commands carry weight because they affect other players, accounts, or the live server.\n\n"
        yield "Use them carefully: create and moderate users, disconnect a player when needed, send an announcement, save the world, or check the server's health.\n\n"
