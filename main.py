from string import ascii_uppercase
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from cataclysm.mechanics_check import check_encounter
from helper.functions import enumerate_step
from helper.log import get_log, get_log_summary
from helper.getter import get_boss_fights
from helper.discord import set_context, set_current_message, update_discord_post
import sys
import asyncio
from sheet.cut_sheet import create_sheet
from sheet.gear_sheet import create_gear_sheet
from sheet.mechanics_sheet import create_mechanics_sheet

load_dotenv(override=True)

bot = commands.Bot()


@bot.slash_command(
    name="cutsheet",
    description="Process warcraftlogs report to a new cut sheet",
    guild_ids=os.getenv("GUILD_IDS").split(","),
)
async def cutsheet(ctx, arg, role=None):
    await ctx.defer()
    set_current_message(await ctx.followup.send("Working..."))
    log = get_log(arg)
    if log.get("error") is not None:
        await ctx.followup.send(log["error"])
    else:
        gear_log = get_log_summary(arg)
        # buff_log = get_log_buffs(arg)
        spreadsheet_id, sheet_id = await create_sheet(log, gear_log, "Cuts")

        await update_discord_post(
            f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sheet_id}"
        )
        if role is not None:
            await ctx.send(f"<@&{role}>")
        else:
            await ctx.send(f"<@{ctx.user.id}>")
    set_current_message(None)


@bot.slash_command(
    name="gearcheck",
    description="Process warcraftlogs report to check player gear",
    guild_ids=os.getenv("GUILD_IDS").split(","),
)
async def gearcheck(ctx, arg, role=None):
    await ctx.defer()
    set_current_message(await ctx.followup.send("Working..."))
    log = get_log(arg)

    if log.get("error") is not None:
        await ctx.followup.send(log["error"])
    else:
        gear_log = get_log_summary(arg)
        # buff_log = get_log_buffs(arg)
        spreadsheet_id = await create_gear_sheet(log, gear_log)

        await update_discord_post(
            f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid=0"
        )
        if role is not None:
            await ctx.send(f"<@&{role}>")
        else:
            await ctx.send(f"<@{ctx.user.id}>")
    set_current_message(None)


@bot.slash_command(
    name="mechanicscheck",
    description="Process warcraftlogs report to check player mechanics prowess",
    guild_ids=os.getenv("GUILD_IDS").split(","),
)
async def mechanicscheck(ctx, arg, role=None):
    set_context(ctx)
    await ctx.defer()
    set_current_message(await ctx.followup.send("Working..."))
    log = get_log(arg)

    if log.get("error") is not None:
        await ctx.followup.send(log["error"])
    else:
        await create_mechanics_sheet(log, arg)

        if role is not None:
            await ctx.send(f"<@&{role}>")
        else:
            await ctx.send(f"<@{ctx.user.id}>")
    set_current_message(None)


@gearcheck.error
@cutsheet.error
@mechanicscheck.error
async def on_application_command_error(
    ctx: discord.ApplicationContext, error: discord.DiscordException
):
    await ctx.followup.send(f"An error occurred during sheet creation: {error}")
    raise error  # Here we raise other errors to ensure they aren't ignored


# TODO: check for flask uptime with "auras/totalUptime" and "auras/totalUses" vs "totalTime"
# def get_log_buffs(report:str):
#     guild_flask_id = 79470 # Incorrect, currently not tracked
#     log_data = requests.get(f'{warcraft_logs_url}tables/buffs/{report}?start=0&end=999999999999&abilityid={guild_flask_id}&by=target&api_key={os.getenv("WCL_USERID")}')
#     return log_data.json()

if __name__ == "__main__":
    # get_wcl_oauth()
    if len(sys.argv) < 2:
        print("Running discord bot")
        bot.run(os.getenv("BOT_TOKEN"))
    else:
        # get_log_v2(sys.argv[1])
        log = get_log(sys.argv[1])
        boss_fights = get_boss_fights(log.get("fights"))
        # print(boss_fights)
        for fight in boss_fights:
            if fight["name"] == "Halfus Wyrmbreaker":
                encounter = check_encounter(sys.argv[1], fight)

        print(encounter)
        # rows = list(ascii_uppercase)
        # enemies = {
        #     encounter[1][enemy]["id"]: rows[idx]
        #     for idx, enemy in enumerate(encounter[1])
        # }

        # ranking = {"damage-done": {}}
        # for enemy in enemies:

        #     ranking["damage-done"][enemy] = {}

        # for idx, entry in enumerate_step(encounter[0], step=2):
        #     for _, enemy in enumerate(entry.get("damage-done", [])):
        #         ranking["damage-done"][enemy["enemyId"]][entry["playerName"]] = {
        #             "totalDamage": enemy.get("totalDamage", 0),
        #             "activeTime": enemy.get("activeTime", 0),
        #         }

        # for encounter in ranking["damage-done"]:
        #     test = sorted(
        #         ranking["damage-done"][encounter].items(),
        #         key=lambda item: item[1]["totalDamage"],
        #         reverse=True,
        #     )[:5]
        #     print(test)
        # print(batch_update_values_request_body)
        # gear_log = get_log_summary(sys.argv[1])
        # buff_log = get_log_buffs(sys.argv[1])
        # loop = asyncio.get_event_loop()

        # players = get_players(gear_log)

        # issues = loop.run_until_complete(update_gear_sheet(None,None,players, log.get("zone")))
        # for issue in issues:
        #     print("###################################################")
        #     print(f"{issue[0]}\n")
        #     print(f"Minor:\n{issue[1]['minor']}")
        #     print(f"Major:\n{issue[1]['major']}")
        #     print(f"Extreme:\n{issue[1]['extreme']}")
