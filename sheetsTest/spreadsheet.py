import gspread
from oauth2client.service_account import ServiceAccountCredentials

newvalues = [1,2,3]

# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

# Find a workbook by name and open the first sheet
# Make sure you use the right name here.
sheet = client.open("visualHelper Log")
sheet_instance = sheet.get_worksheet(0)
sheet_instance.append_row(newvalues)

# Extract and print all of the values
singleCell = sheet_instance.cell(col=1,row=2)
print(singleCell)
