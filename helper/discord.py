current_message = None
context = None


def set_context(ctx):
    global context
    context = ctx


def set_current_message(msg):
    global current_message
    current_message = msg


async def update_discord_post(msg):
    global current_message
    if current_message is not None:
        await current_message.edit(content=msg)


async def send_discord_post(msg):
    global context
    if context is not None:
        await context.send(f"{msg}")


def check_message(author, encounters):
    def inner_check(msg):
        if msg.author != author:
            return False
        checks = msg.content.split(",")
        for check in checks:
            mod: list = check.split("-")
            # print(mod)
            if len(mod) == 1:
                if mod[0] in ["A", "B", "C", "D"]:
                    continue
                elif "." not in mod[0]:
                    return False
            # msg contains a modifier like A- or B-
            if len(mod) > 1:
                if mod[0] not in ["A", "B", "C", "D"]:
                    return False
                mod[0] = mod[1]
                mod.pop()
            # print(mod)
            try:
                if "." in mod[0]:
                    temp1, temp2 = mod[0].split(".")
                    mod[0] = temp1
                    mod.append(int(temp2))
                mod[0] = int(mod[0])
                # print(mod)
            except Exception as e:
                print(e)
                return False

            encounter_fights = {}
            for encounter in encounters:
                encounter_fights[encounters[encounter]["id"]] = len(
                    encounters[encounter]["fights"]
                )

            if mod[0] > len(encounters) or mod[0] < 1:
                return False
            if len(mod) > 1:
                if mod[1] > encounter_fights.get(mod[0], len(encounters)) or mod[1] < 1:
                    return False
        return True

    return inner_check
