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
