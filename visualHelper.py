from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

import os
from datetime import datetime
from picamera import PiCamera
from time import sleep
from gtts import gTTS
import gspread
from oauth2client.service_account import ServiceAccountCredentials


language = 'en'
camera = PiCamera()

subscription_key = "bf269afc8c1d44ea95beae73a6fb1890"
endpoint = "https://scenedetection.cognitiveservices.azure.com/"
computervisionClient = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

imagePath = "/home/pi/visualHelper/images/image.jpg"
lastCaption = ""

scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)
sheet = client.open("visualHelper Log")
sheetInstance = sheet.get_worksheet(0)


# Find the amount of similar words between two sentences and give it a similarity score from 0 to 1
def GetSimilarity(str1, str2):
    a = set(str1.split())
    b = set(str2.split())
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))


print("Entries with confidence below 0.35:")
logData  = sheetInstance.get_all_records()
for c in logData:
    date = c["Date and Time"]
    caption = c["Caption"]
    score = float(c["Confidence"])
    if score < 0.35:
        print(f"{date}  {caption}  {score}" )

#Get log file links and add to Apache site
linkFile = open("/var/www/html/index.html", "w")
linkFile.write("<html>\n<body>\n")
for c in logData:
    caption = c["Caption"]
    date = c["Date and Time"]
    link = c["Link"]
    score = float(c["Confidence"])
    linkFile.write(f'<a href="{link}">{caption} on {date} with confidence {score}</a><p></p>\n')
linkFile.write("</body>\n</html>")
linkFile.close()

print("")

print("===== Visual Helper Started =====")
while True:
    camera.capture(imagePath)
    imageHandler = open(imagePath, "rb")

    # Call computer vision api
    try:
        descriptionResults = computervisionClient.describe_image_in_stream(imageHandler)
    except:
        print("API call failed")

    # Process and speak the captions received
    if len(descriptionResults.captions) == 0:
        print("No description detected.")

    else:
        for caption in descriptionResults.captions:
            if caption.confidence <= 0.1:
                print("I'm not sure how to describe that photo. Please try again.")

            else:
                if GetSimilarity(caption.text, lastCaption) < 0.6:
                    print("'{}' with confidence {:.2f}%".format(caption.text, caption.confidence * 100))
                    try:
                        # Speak the caption
                        speak = gTTS(text=caption.text, lang=language, slow=False)
                        speak.save("caption.mp3")
                        os.system("mpg321 caption.mp3")
                    except:
                        print("Speaking failed")
                    # Add info to logs
                    time = datetime.now()
                    dateString = time.strftime("%d-%m-%Y at %H:%M:%S")
                    newPath = f"/var/www/html/vision/pics/{dateString}.jpg"
                    link = f"/vision/pics/{dateString}.jpg"
                    os.rename(imagePath, newPath)
                    confidence = "{:.2f}".format(caption.confidence) 
                    log = [dateString,caption.text,confidence,link]
                    sheetInstance.append_row(log)

                    # Add new links to Apache site
                    linkFile = open("/var/www/html/index.html")
                    fileList = linkFile.readlines()
                    linkFile.close()
                    fileList = fileList[:-2]
                    fileList.append(f'<a href="{link}">{caption.text} on {dateString} with confidence {confidence}</a><p></p>\n')
                    fileList.append("</body>\n</html>")
                    newLinks = "".join(fileList)
                    linkFile = open("/var/www/html/index.html","w")
                    linkFile.write(newLinks)
                    linkFile.close()

                    lastCaption = caption.text
    sleep(3)
