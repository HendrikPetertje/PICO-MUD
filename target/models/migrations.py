def rooms_schema(rooms):
    changed = False
    data = []
    for room in rooms.data:
        room_copy = room.copy()
        if "unlocked_if" not in room_copy:
            room_copy["unlocked_if"] = []
            changed = True
        items = []
        for item in room_copy.get("items", []):
            item_copy = item.copy()
            if "visible_if" not in item_copy:
                item_copy["visible_if"] = []
                changed = True
            actions = []
            for action in item_copy.get("interactions", []):
                action_copy = action.copy()
                if "available_if" not in action_copy:
                    action_copy["available_if"] = []
                    changed = True
                actions.append(action_copy)
            item_copy["interactions"] = actions
            items.append(item_copy)
        room_copy["items"] = items
        data.append(room_copy)
    if changed:
        rooms.publish(data)
    return changed


def apply(rooms):
    return rooms_schema(rooms)
