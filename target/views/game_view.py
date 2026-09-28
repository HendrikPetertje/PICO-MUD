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
    result = action["action"]
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
    yield "/" + verb + (" " + syntax if syntax else "") + " [" + permission + "]\n"
    if detailed:
        if aliases:
            yield "Aliases: " + aliases + "\n"
        yield description + "\n"


def tutorial():
    yield "PICO MUD tutorial\n\n"
    yield "Moving\n"
    yield "Guests and users can explore public rooms with /go north or /n. "
    yield "Use /join <player> to visit an online player when their room is accessible. "
    yield "Use /teleport to <room_id> for a known room, or /teleport global home to return to room 1. "
    yield "Registered users can also use /home for their own home room.\n\n"
    yield "Building rooms\n"
    yield "Registered users can build only in rooms they own. Create a connected room with "
    yield '/dig north "green garden", then enter it with /n. Name and describe the new room '
    yield 'with /rename here "The Green Garden" and /describe here A quiet place to rest.\n\n'
    yield "Items and actions\n"
    yield "In a room you own, create scenery with /create \"brass lever\". Add a message-only "
    yield 'action with /interaction add "brass lever" pull The floor creaks. Visitors can use it '
    yield 'with /pull "brass lever". Add a separate portal action with /interaction add "brass lever" enter '
    yield 'You step through the gate, then /interaction teleport "brass lever" enter <room_id>. '
    yield "A portal may target your own room or another owner's public room, but not their private room.\n\n"
    yield "Creatures and habbits\n"
    yield "Items can become creatures: create one, then run /creature \"garden sprite\" on. "
    yield "Creatures keep the same item interactions. "
    yield 'Give it timed activity with /habbit add "garden sprite" 30 hum, then configure output '
    yield 'with /habbit edit "garden sprite" 1 emote on hums softly. Use /habbits "garden sprite" '
    yield "to review its activity. Habbits run only while players are in the room.\n"
