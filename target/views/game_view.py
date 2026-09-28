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


def action_entry(action, detailed=False):
    result = action["action"]
    if detailed:
        result += ": " + action["flavor_text"]
        if "teleport_to_room_id" in action:
            result += " -> room " + str(action["teleport_to_room_id"])
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
