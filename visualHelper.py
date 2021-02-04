from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from azure.cognitiveservices.vision.computervision.models import VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials

import os
from picamera import PiCamera
from time import sleep
from gtts import gTTS

language = 'en'
camera = PiCamera()
subscription_key = "bf269afc8c1d44ea95beae73a6fb1890"
endpoint = "https://scenedetection.cognitiveservices.azure.com/"
computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))

imagePath = "/home/pi/visualHelper/images/image.jpg"
lastCaption = ""


# Find the amount of similar words between two sentences and give it a similarity score from 0 to 1
def get_similarity(str1, str2):
    a = set(str1.split())
    b = set(str2.split())
    c = a.intersection(b)
    return float(len(c)) / (len(a) + len(b) - len(c))


print("===== Visual Helper Started =====")

while True:
    camera.capture(imagePath)
    imageHandler = open(imagePath, "rb")

    # Call computer vision api
    try:
        description_results = computervision_client.describe_image_in_stream(imageHandler)
    except:
        print("API call failed")

    # Process and speak the captions received
    if len(description_results.captions) == 0:
        print("No description detected.")

    else:
        for caption in description_results.captions:
            if caption.confidence <= 0.1:
                print("I'm not sure how to describe that photo. Please try again.")

            else:
                if get_similarity(caption.text, lastCaption) < 0.6:
                    print("'{}' with confidence {:.2f}%".format(caption.text, caption.confidence * 100))
                    try:
                        # Speak the caption
                        speak = gTTS(text=caption.text, lang=language, slow=False)
                        speak.save("caption.mp3")
                        os.system("mpg321 caption.mp3")
                    except:
                        print("Speaking failed")
                    lastCaption = caption.text
    sleep(3)

