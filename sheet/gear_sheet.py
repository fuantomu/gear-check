from gear_check import check_gear, load_enchants
from helper.credentials import get_creds
from helper.functions import post_players
from helper.getter import get_players, get_unique_players
from helper.discord import send_discord_post, update_discord_post
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
from sheet.general import (
    find_sheet_id,
    get_sheet_ids,
    update_alignment,
    update_background_color,
    update_cell_width,
    update_class_color,
    update_text_format,
    update_wrap,
)

_sheets = None


async def create_gear_sheet(log, gear_log):
    creds = get_creds()

    try:
        await update_discord_post(f"Creating Google Sheet")
        service = build("sheets", "v4", credentials=creds)
        title = f"{log.get('title')} Gear Sheet"
        spreadsheet = {"properties": {"title": title}}
        spreadsheet = (
            service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )
        players = get_players(gear_log)

        await send_discord_post(
            f"https://docs.google.com/spreadsheets/d/{spreadsheet.get('spreadsheetId')}/edit#gid=0"
        )

        global _sheets
        _sheets = get_sheet_ids(service, spreadsheet.get("spreadsheetId"))

        service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet.get("spreadsheetId"),
            body={
                "requests": [
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": find_sheet_id(_sheets, "Sheet1"),
                                "title": "Gearcheck",
                            },
                            "fields": "title",
                        }
                    }
                ]
            },
        ).execute()

        await update_gear_sheet(
            service,
            spreadsheet.get("spreadsheetId"),
            players,
            log.get("zone"),
            "Gearcheck",
        )

        # Connect to Google Drive and make spreadsheet public
        await update_discord_post(f"Making Google Sheet public")
        drive_client = build("drive", "v3", credentials=creds)

        files = (
            drive_client.files()
            .list(
                q=f"name contains '{title}'",
                spaces="drive",
                fields="nextPageToken, files(id, name)",
            )
            .execute()
            .get("files")
        )

        user_permission = {"type": "anyone", "role": "writer"}
        drive_client.permissions().create(
            fileId=files[0]["id"],
            body=user_permission,
            fields="id",
        ).execute()

        await update_discord_post(f"Parsing players to database")
        post_players(
            [
                (player["name"], player["server"])
                for player in get_unique_players(players)
            ]
        )

        await update_discord_post(
            f"Finished processing gear of {len(players)} player(s)"
        )

    except HttpError as error:
        print(f"An error occurred: {error}")


async def update_gear_sheet(
    service, spreadsheetId, players, zone, sheet_title="Sheet1"
):
    load_enchants()

    gear_issues = []
    for character in players:
        # player_buffs = [buff for buff in buffs['auras'] if buff['name'] == character.get('name')] or [{}]
        # player_buffs[0]['totalTime'] = buffs['totalTime']
        # print(player_buffs)
        await update_discord_post(f"Checking gear of player {character.get('name')}")
        gear_issues.append(check_gear(character, zone))

    batch_update_values_request_body = {
        "valueInputOption": "RAW",
        "data": [
            {
                "range": f"{sheet_title}!A1",
                "majorDimension": "COLUMNS",
                "values": [["Character - Spec"]],
            },
            {
                "range": f"{sheet_title}!A2",
                "majorDimension": "COLUMNS",
                "values": [
                    [
                        f'{character.get("name")} - {character.get("specs",[])[0]}'
                        for character in players
                    ]
                ],
            },
            {
                "range": f"{sheet_title}!B1",
                "majorDimension": "COLUMNS",
                "values": [["Potions"]],
            },
            {
                "range": f"{sheet_title}!B2",
                "majorDimension": "COLUMNS",
                "values": [[f'{character["potionUse"]}' for character in players]],
            },
            {
                "range": f"{sheet_title}!C1",
                "majorDimension": "COLUMNS",
                "values": [["Healthstones"]],
            },
            {
                "range": f"{sheet_title}!C2",
                "majorDimension": "COLUMNS",
                "values": [[f'{character["healthstoneUse"]}' for character in players]],
            },
            {
                "range": f"{sheet_title}!D1",
                "majorDimension": "COLUMNS",
                "values": [["Gear issues (minor)"]],
            },
            {
                "range": f"{sheet_title}!D2",
                "majorDimension": "COLUMNS",
                "values": [[issue["minor"] for issue in gear_issues]],
            },
            {
                "range": f"{sheet_title}!E1",
                "majorDimension": "COLUMNS",
                "values": [["Gear issues (major)"]],
            },
            {
                "range": f"{sheet_title}!E2",
                "majorDimension": "COLUMNS",
                "values": [[issue["major"] for issue in gear_issues]],
            },
            {
                "range": f"{sheet_title}!F1",
                "majorDimension": "COLUMNS",
                "values": [["Gear issues (extreme)"]],
            },
            {
                "range": f"{sheet_title}!F2",
                "majorDimension": "COLUMNS",
                "values": [[issue["extreme"] for issue in gear_issues]],
            },
        ],
    }

    await update_discord_post(f"Updating Gear Sheet")

    try:
        service.spreadsheets().values().batchUpdate(
            spreadsheetId=spreadsheetId, body=batch_update_values_request_body
        ).execute()
    except:
        return zip([player["name"] for player in players], gear_issues)

    global _sheets
    if _sheets is None:
        _sheets = get_sheet_ids(service, spreadsheetId)
    sheet_id = find_sheet_id(_sheets, sheet_title)

    update_class_color(service, spreadsheetId, players, sheetId=sheet_id)
    update_background_color(
        service,
        spreadsheetId,
        {
            "row_start": 1,
            "row_end": 1 + len(players),
            "column_start": 3,
            "column_end": 4,
        },
        {"red": 1, "green": 1, "blue": 0},
        sheetId=sheet_id,
    )
    update_background_color(
        service,
        spreadsheetId,
        {
            "row_start": 1,
            "row_end": 1 + len(players),
            "column_start": 4,
            "column_end": 5,
        },
        {"red": 1, "green": 0.6, "blue": 0},
        sheetId=sheet_id,
    )
    update_background_color(
        service,
        spreadsheetId,
        {
            "row_start": 1,
            "row_end": 1 + len(players),
            "column_start": 5,
            "column_end": 6,
        },
        {"red": 0.918, "green": 0.3412, "blue": 0.3412},
        sheetId=sheet_id,
    )
    update_cell_width(service, spreadsheetId, sheetId=sheet_id)
    update_wrap(
        service,
        spreadsheetId,
        {
            "row_start": 1,
            "row_end": 1 + len(players),
            "column_start": 1,
            "column_end": 6,
        },
        sheetId=sheet_id,
    )
    update_text_format(
        service,
        spreadsheetId,
        {
            "row_start": 0,
            "row_end": 1 + len(players),
            "column_start": 0,
            "column_end": 6,
        },
        sheetId=sheet_id,
    )
    update_alignment(
        service,
        spreadsheetId,
        {"row_start": 0, "row_end": 1, "column_start": 0, "column_end": 6},
        sheetId=sheet_id,
    )
    update_alignment(
        service,
        spreadsheetId,
        {
            "row_start": 1,
            "row_end": 1 + len(players),
            "column_start": 0,
            "column_end": 3,
        },
        sheetId=sheet_id,
    )
