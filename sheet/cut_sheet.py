from helper.credentials import get_creds
from helper.getter import get_players, get_unique_players
from helper.discord import send_discord_post, update_discord_post
from sheet.gear_sheet import update_gear_sheet
from sheet.general import find_sheet_id, get_sheet_ids, update_class_color
from googleapiclient.errors import HttpError
from googleapiclient.discovery import build
import os

_sheets = None


async def create_sheet(log, gear_log, sheet_title):
    creds = get_creds()

    try:
        await update_discord_post(f"Creating Google Sheet")
        service = build("sheets", "v4", credentials=creds)
        title = f"{log.get('title')} Gold Cut Sheet"
        spreadsheet = {"properties": {"title": title}}
        spreadsheet = (
            service.spreadsheets()
            .create(body=spreadsheet, fields="spreadsheetId")
            .execute()
        )
        players = get_players(gear_log)
        unique_players = get_unique_players(players)

        await send_discord_post(
            f"https://docs.google.com/spreadsheets/d/{spreadsheet.get('spreadsheetId')}/edit#gid=0"
        )

        update_class_color(
            service,
            os.getenv("SOURCE_SPREADSHEET"),
            unique_players,
            sheetId=os.getenv("SOURCE_SHEET"),
            offsetRow=5,
        )
        update_class_color(
            service,
            os.getenv("SOURCE_SPREADSHEET"),
            unique_players,
            sheetId=os.getenv("SOURCE_SHEET"),
            offsetRow=5,
            offsetColumnStart=6,
            offsetColumnEnd=11,
        )
        copy_sheet = (
            service.spreadsheets()
            .sheets()
            .copyTo(
                spreadsheetId=os.getenv("SOURCE_SPREADSHEET"),
                sheetId=os.getenv("SOURCE_SHEET"),
                body={"destinationSpreadsheetId": spreadsheet.get("spreadsheetId")},
            )
            .execute()
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
                                "sheetId": copy_sheet.get("sheetId"),
                                "title": sheet_title,
                            },
                            "fields": "title",
                        }
                    },
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": find_sheet_id(_sheets, "Sheet1"),
                                "title": "Gearcheck",
                            },
                            "fields": "title",
                        }
                    },
                ]
            },
        ).execute()

        await update_sheet(
            service, spreadsheet.get("spreadsheetId"), sheet_title, unique_players
        )
        await update_gear_sheet(
            service,
            spreadsheet.get("spreadsheetId"),
            players,
            log.get("zone"),
            sheet_title="Gearcheck",
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

        await update_discord_post(
            f"Finished processing cutsheet for {len(players)} player(s)"
        )

    except HttpError as error:
        print(f"An error occurred: {error}")


async def update_sheet(service, spreadsheetId, sheet_title, players):
    await update_discord_post(f"Updating Cut sheet")
    batch_update_values_request_body = {
        "valueInputOption": "RAW",
        "data": [
            {
                "range": f"{sheet_title}!A6",
                "majorDimension": "COLUMNS",
                "values": [
                    [f'{player["name"]}-{player["server"]}' for player in players]
                ],
            }
        ],
    }

    service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheetId, body=batch_update_values_request_body
    ).execute()
