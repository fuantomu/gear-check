import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from gear_check import check_gear
import sys
load_dotenv(override=True)

scopes = ["https://www.googleapis.com/auth/spreadsheets",'https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/drive.metadata','https://www.googleapis.com/auth/drive.file',]
bot = commands.Bot()

@bot.slash_command(
  name="cutsheet",
  description="Process warcraftlogs report to a new cut sheet",
  guild_ids=os.getenv('GUILD_IDS').split(",")
)
async def cutsheet(ctx, arg):
    await ctx.defer()
    log = get_log(arg)
    if log.get("error") is not None:
        await ctx.followup.send(log["error"])
    else:
        gear_log = get_log_summary(arg)
        spreadsheet_id, sheet_id = create_sheet(log, gear_log, "Cuts")
        
        await ctx.followup.send(f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sheet_id}')
    
@bot.slash_command(
  name="gearcheck",
  description="Process warcraftlogs report to check player gear",
  guild_ids=os.getenv('GUILD_IDS').split(",")
)
async def gearcheck(ctx, arg):
    await ctx.defer()
    log = get_log(arg)

    if log.get("error") is not None:
        await ctx.followup.send(log["error"])
    else:
        gear_log = get_log_summary(arg)
        spreadsheet_id = create_gear_sheet(log, gear_log)
        
        await ctx.followup.send(f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid=0')

@gearcheck.error
@cutsheet.error
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    await ctx.followup.send(f'An error occurred during sheet creation: {error}')
    raise error  # Here we raise other errors to ensure they aren't ignored

warcraft_logs_url = 'https://www.warcraftlogs.com:443/v1/report/'
def get_log(report:str):
    log_data = requests.get(f'{warcraft_logs_url}fights/{report}?api_key={os.getenv("WCL_USERID")}')
    return log_data.json()

def get_log_summary(report:str):
    log_data = requests.get(f'{warcraft_logs_url}tables/summary/{report}?start=0&end=999999999999&api_key={os.getenv("WCL_USERID")}')
    return log_data.json().get("playerDetails")

def get_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds
    
def create_sheet(log, gear_log, sheet_title):
    creds = get_creds()

    try:
        service = build('sheets', 'v4', credentials=creds)
        title = f"{log.get('title')} Gold Cut Sheet"
        spreadsheet = {
            'properties': {
                'title': title
            }
        }        
        spreadsheet = service.spreadsheets().create(body=spreadsheet,fields='spreadsheetId').execute()
        copy_sheet = service.spreadsheets().sheets().copyTo(spreadsheetId = os.getenv("SOURCE_SPREADSHEET"), sheetId=os.getenv("SOURCE_SHEET"),body={"destinationSpreadsheetId": spreadsheet.get('spreadsheetId')}).execute()
        service.spreadsheets().batchUpdate(spreadsheetId=spreadsheet.get('spreadsheetId'), body={"requests": [{"updateSheetProperties":{ "properties": {"sheetId": copy_sheet.get('sheetId'), "title": sheet_title}, "fields": "title"}}]}).execute()
        update_sheet(service, spreadsheet.get('spreadsheetId'), sheet_title, log)
        update_gear_sheet(service, spreadsheet.get('spreadsheetId'), gear_log, log.get("zone"), sheet_title="Sheet1")
        
        # Connect to Google Drive and make spreadsheet public
        drive_client = build('drive', 'v3', credentials=creds)
        
        files = drive_client.files().list(q=f"name contains '{title}'",spaces="drive",fields="nextPageToken, files(id, name)").execute().get('files')
        
        user_permission = {
            "type": "anyone",
            "role": "writer"
        }
        drive_client.permissions().create(
                fileId=files[0]['id'],
                body=user_permission,
                fields="id",
        ).execute()

        return spreadsheet.get('spreadsheetId'), copy_sheet.get('sheetId')
    except HttpError as error:
        print(f"An error occurred: {error}")
    
def create_gear_sheet(log, gear_log):
    creds = get_creds()

    try:
        service = build('sheets', 'v4', credentials=creds)
        title = f"{log.get('title')} Gear Sheet"
        spreadsheet = {
            'properties': {
                'title': title
            }
        }        
        spreadsheet = service.spreadsheets().create(body=spreadsheet,fields='spreadsheetId').execute()
        update_gear_sheet(service, spreadsheet.get('spreadsheetId'), gear_log, log.get("zone"))
        
        # Connect to Google Drive and make spreadsheet public
        drive_client = build('drive', 'v3', credentials=creds)
        
        files = drive_client.files().list(q=f"name contains '{title}'",spaces="drive",fields="nextPageToken, files(id, name)").execute().get('files')
        
        user_permission = {
            "type": "anyone",
            "role": "writer"
        }
        drive_client.permissions().create(
                fileId=files[0]['id'],
                body=user_permission,
                fields="id",
        ).execute()

        return spreadsheet.get('spreadsheetId')
    except HttpError as error:
        print(f"An error occurred: {error}")
    
def update_sheet(service, spreadsheetId, sheet_title, log):
    batch_update_values_request_body = {
        "valueInputOption": "RAW",
        "data": [
            {
                'range': f'{sheet_title}!A6',
                'majorDimension': 'COLUMNS',
                'values': [[character["name"] for character in log.get("exportedCharacters")]]
            }
        ]
    }
    service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheetId, body=batch_update_values_request_body).execute()

#   name
#   id
#   guid
#   type (class)
#   server
#   icon
#   specs
#   minItemLevel
#   maxItemLevel
#   potionUse
#   healthstoneUse
#   combatantInfo
#       stats
#       talents
#       artifacts
#       gear
#           id
#           slot
#           quality
#           icon
#           name
#           itemLevel
#           permanentEnchant
#           permanentEnchantName
#           gems
#               id
#               itemLevel
#               icon
#       specIDs
#       factionID
def update_gear_sheet(service, spreadsheetId, gear, zone, sheet_title = "Sheet1"):
    players = []
    players.extend([character for character in gear["tanks"] if character.get("combatantInfo") != {}])
    players.extend([character for character in gear["healers"] if character.get("combatantInfo") != {}])
    players.extend([character for character in gear["dps"] if character.get("combatantInfo") != {}])

    gear_issues = [check_gear(character["combatantInfo"]["gear"], zone, character["specs"][0]) for character in players]

    batch_update_values_request_body = {
        "valueInputOption": "RAW",
        "data": [
            {
                'range': f"{sheet_title}!A1",
                'majorDimension': "COLUMNS",
                'values': [["Character - Spec"]]
            },
            {
                'range': f'{sheet_title}!A2',
                'majorDimension': 'COLUMNS',
                'values': [[f'{character.get("name")} - {character.get("specs",[])[0]}' for character in players]]
            },
            {
                'range': f"{sheet_title}!B1",
                'majorDimension': "COLUMNS",
                'values': [["Potions"]]
            },
            {
                'range': f'{sheet_title}!B2',
                'majorDimension': 'COLUMNS',
                'values': [[f'{character["potionUse"]}' for character in players]]
            },
            {
                'range': f"{sheet_title}!C1",
                'majorDimension': "COLUMNS",
                'values': [["Healthstones"]]
            },
            {
                'range': f'{sheet_title}!C2',
                'majorDimension': 'COLUMNS',
                'values': [[f'{character["healthstoneUse"]}' for character in players]]
            },
            {
                'range': f"{sheet_title}!D1",
                'majorDimension': "COLUMNS",
                'values': [["Gear issues (minor)"]]
            },
            {
                'range': f'{sheet_title}!D2',
                'majorDimension': 'COLUMNS',
                'values': [[issue["minor"] for issue in gear_issues]]
            },
            {
                'range': f"{sheet_title}!E1",
                'majorDimension': "COLUMNS",
                'values': [["Gear issues (major)"]]
            },
            {
                'range': f'{sheet_title}!E2',
                'majorDimension': 'COLUMNS',
                'values': [[issue["major"] for issue in gear_issues]]
            },
            {
                'range': f"{sheet_title}!F1",
                'majorDimension': "COLUMNS",
                'values': [["Gear issues (extreme)"]]
            },
            {
                'range': f'{sheet_title}!F2',
                'majorDimension': 'COLUMNS',
                'values': [[issue["extreme"] for issue in gear_issues]]
            }
        ]
    }
    
    try:
        service.spreadsheets().values().batchUpdate(spreadsheetId=spreadsheetId, body=batch_update_values_request_body).execute()
    except:
        return zip([player["name"] for player in players], gear_issues)
    
    update_class_color(service, spreadsheetId, players)
    update_background_color(service, spreadsheetId, {"row_start": 1, "row_end": 1+len(players), "column_start": 3, "column_end": 4}, {"red": 1, "green": 1, "blue": 0})
    update_background_color(service, spreadsheetId, {"row_start": 1, "row_end": 1+len(players), "column_start": 4, "column_end": 5}, {"red": 1, "green": 0.6, "blue": 0})
    update_background_color(service, spreadsheetId, {"row_start": 1, "row_end": 1+len(players), "column_start": 5, "column_end": 6}, {"red": 0.918, "green": 0.3412, "blue": 0.3412})
    update_cell_width(service, spreadsheetId)
    update_wrap(service, spreadsheetId, {"row_start": 1, "row_end": 1+len(players), "column_start": 1, "column_end": 6})
    update_text_format(service, spreadsheetId, {"row_start": 0, "row_end": 1+len(players), "column_start": 0, "column_end": 6})
    update_alignment(service, spreadsheetId, {"row_start": 0, "row_end": 1, "column_start": 0, "column_end": 6})
    update_alignment(service, spreadsheetId, {"row_start": 1, "row_end": 1+len(players), "column_start": 0, "column_end": 3})

def update_class_color(service, spreadsheetId, players):
    class_colors = {
        "Warrior": {"red": 198, "green": 155, "blue": 109},
        "Hunter": {"red": 170, "green": 211, "blue": 114},
        "Warlock": {"red": 135, "green": 136, "blue": 238},
        "Druid": {"red": 255, "green": 124, "blue": 10},
        "Mage": {"red": 63, "green": 199, "blue": 235},
        "Rogue": {"red": 252, "green": 252, "blue": 2},
        "Priest": {"red": 255, "green": 255, "blue": 254},
        "Shaman": {"red": 31, "green": 105, "blue": 235},
        "Paladin": {"red": 244, "green": 140, "blue": 186},
        "DeathKnight": {"red": 196, "green": 30, "blue": 58}
    }
    request_body = [
        {
            "repeatCell":{
                "cell":
                {
                    "userEnteredFormat":
                    {
                        "backgroundColor":
                        {
                            "red": class_colors[player["type"]].get("red",255)/255,
                            "green": class_colors[player["type"]].get("green",255)/255,
                            "blue": class_colors[player["type"]].get("blue",255)/255
                        }
                    }
                },
                "fields":"userEnteredFormat.backgroundColor",
                "range":{
                    "sheetId": 0,
                    "startRowIndex": index+1,
                    "endRowIndex": index+2,
                    "startColumnIndex": 0,
                    "endColumnIndex": 1
                }
            }
        }
        for index,player in enumerate(players)
    ]

    body = {
        "requests": request_body
    }

    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

def update_background_color(service, spreadsheetId, range, color):
    request_body = {
        "repeatCell":{
            "cell":
            {
                "userEnteredFormat":
                {
                    "backgroundColor":
                    {
                        "red": color.get("red",0),
                        "green": color.get("green",0),
                        "blue": color.get("blue",0)
                    }
                }
            },
            "fields":"userEnteredFormat.backgroundColor",
            "range":{
                "sheetId": 0,
                "startRowIndex": range.get("row_start",0),
                "endRowIndex": range.get("row_end",range.get("row_start",0)+1),
                "startColumnIndex": range.get("column_start",0),
                "endColumnIndex": range.get("column_end",0)
            }
        }
    }

    body = {
        "requests": request_body
    }

    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()
    
def update_cell_width(service, spreadsheetId):
    column_widths = [
        {"columnNumber": 1, "width": 180},
        {"columnNumber": 2, "width": 120},
        {"columnNumber": 3, "width": 120},
        {"columnNumber": 4, "width": 600},
        {"columnNumber": 5, "width": 600},
        {"columnNumber": 6, "width": 600},
    ]
    request_body = [
        {
            "updateDimensionProperties": {
                "properties": {"pixelSize": e["width"]},
                "range": {
                    "dimension": "COLUMNS",
                    "sheetId": 0,
                    "startIndex": e["columnNumber"] - 1,
                    "endIndex": e["columnNumber"],
                },
                "fields": "pixelSize",
            }
        }
        for e in column_widths
    ]

    body = {
        "requests": request_body
    }
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()
    
def update_wrap(service, spreadsheetId, range):
    request_body = [
        {
            "repeatCell": {
                "range":{
                    "sheetId": 0,
                    "startRowIndex": range.get("row_start",0),
                    "endRowIndex": range.get("row_end",range.get("row_start",0)+1),
                    "startColumnIndex": range.get("column_start",0),
                    "endColumnIndex": range.get("column_end",0)
                },
                "cell": 
                    {
                        "userEnteredFormat": {
                            "wrapStrategy": "WRAP"
                        }
                    }
                ,
                "fields": "userEnteredFormat.wrapStrategy"
            }
        }
    ]

    body = {
        "requests": request_body
    }
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()
    
def update_text_format(service, spreadsheetId, range):
    request_body = [
        {
            "repeatCell": {
                "range":{
                    "sheetId": 0,
                    "startRowIndex": range.get("row_start",0),
                    "endRowIndex": range.get("row_end",range.get("row_start",0)+1),
                    "startColumnIndex": range.get("column_start",0),
                    "endColumnIndex": range.get("column_end",0)
                },
                "cell": 
                    {
                        "textFormatRuns": [{
                            "startIndex": 0,
                            "format": {
                                "fontFamily": "Roboto"
                            }
                        }]
                    }
                ,
                "fields": "textFormatRuns"
            }
        },
        {
            "repeatCell": {
                "range":{
                    "sheetId": 0,
                    "startRowIndex": 0,
                    "endRowIndex": 1,
                    "startColumnIndex": 0,
                    "endColumnIndex": 6
                },
                "cell": 
                    {
                        "textFormatRuns": [{
                            "startIndex": 0,
                            "format": {
                                "bold": True,
                                "fontSize": 14
                            }
                        }]
                    }
                ,
                "fields": "textFormatRuns"
            }
        }
    ]

    body = {
        "requests": request_body
    }
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()
    
def update_alignment(service, spreadsheetId, range):
    request_body = [
        {
            "repeatCell": {
                "range":{
                    "sheetId": 0,
                    "startRowIndex": range.get("row_start",0),
                    "endRowIndex": range.get("row_end",range.get("row_start",0)+1),
                    "startColumnIndex": range.get("column_start",0),
                    "endColumnIndex": range.get("column_end",0)
                },
                "cell": 
                    {
                        "userEnteredFormat": {
                            "horizontalAlignment": "CENTER",
                            "verticalAlignment": "MIDDLE"
                        }
                    }
                ,
                "fields": "userEnteredFormat.horizontalAlignment,userEnteredFormat.verticalAlignment"
            }
        }
    ]

    body = {
        "requests": request_body
    }
    service.spreadsheets().batchUpdate(spreadsheetId=spreadsheetId, body=body).execute()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Running discord bot")
        bot.run(os.getenv('BOT_TOKEN'))
    else:
        issues = update_gear_sheet(None,None, get_log_summary(sys.argv[1]), get_log(sys.argv[1]).get("zone"))
        for issue in issues:
            print("###################################################")
            print(f"{issue[0]}\n")
            print(f"Minor:\n{issue[1]['minor']}")
            print(f"Major:\n{issue[1]['major']}")
            print(f"Extreme:\n{issue[1]['extreme']}")