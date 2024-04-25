from discord.ext import commands
import os
from dotenv import load_dotenv
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
load_dotenv()

scopes = ["https://www.googleapis.com/auth/spreadsheets",'https://www.googleapis.com/auth/drive','https://www.googleapis.com/auth/drive.metadata','https://www.googleapis.com/auth/drive.file',]
bot = commands.Bot()

@bot.slash_command(
  name="cutsheet",
  description="Process warcraftlogs report to a new cut sheet",
  guild_ids=[os.getenv('GUILD_ID')]
)
async def cutsheet(ctx, arg):
    await ctx.defer()
    log = get_log(arg)
    if log.get("exportedCharacters", []) == 0:
        await ctx.respond(log.get('error'))
        return
    try:
        spreadsheet_id, sheet_id = create_sheet(log, "Cuts")
    except Exception as e:
        await ctx.respond(f'An error occurred during sheet creation: {str(e)}')
        return
    
    await ctx.followup.send(f'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/edit#gid={sheet_id}')

warcraft_logs_url = 'https://www.warcraftlogs.com:443/v1/report/fights/'
def get_log(report:str):
    log_data = requests.get(f'{warcraft_logs_url}{report}?api_key={os.getenv("WCL_USERID")}')
    return log_data.json()
    
def create_sheet(log, sheet_title):
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
        raise
    
def update_sheet(service, spreadsheetId, sheet_title, log):
    print(log.get("exportedCharacters"))
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
    
bot.run(os.getenv('BOT_TOKEN'))