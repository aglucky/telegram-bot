from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from msrest.authentication import CognitiveServicesCredentials
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes

import cv2
from functools import cmp_to_key
import numpy as np
import os
from dotenv import load_dotenv
import requests
import time

# Function to perform sorting
def countDistinct(s):
    m = {}
    for i in range(len(s)):
        if s[i] not in m:
            m[s[i]] = 1
        else:
            m[s[i]] += 1
    return len(m)
def compare(a, b):
    return (countDistinct(b) - countDistinct(a))
    
def get_client():
    load_dotenv('.env')
    subscription_key = os.getenv('OCR_KEY')
    endpoint = "https://ocr-wordle.cognitiveservices.azure.com"
    computervision_client = ComputerVisionClient(endpoint, CognitiveServicesCredentials(subscription_key))
    return computervision_client

def read_image(path):
    computervision_client = get_client()
    with open(path, 'rb') as f:
        read_response = computervision_client.read_in_stream(f, raw=True)

    read_operation_location = read_response.headers["Operation-Location"]
    operation_id = read_operation_location.split("/")[-1]

    while True:
        read_result = computervision_client.get_read_result(operation_id)
        if read_result.status.lower() not in ['notstarted', 'running']:
            break
        time.sleep(1)
    # Get the detected text
    text = ""
    if read_result.status == OperationStatusCodes.succeeded:
        for page in read_result.analyze_result.read_results:
            for line in page.lines:
                text += line.text
    return text

def contour_sort(a, b):
    br_a = cv2.boundingRect(a)
    br_b = cv2.boundingRect(b)
    if abs(br_a[1] - br_b[1]) <= 15:
        return br_a[0] - br_b[0]
    return br_a[1] - br_b[1]

#TODO add support for iphone screenshots
def process_image(path):
    #Get contours with wordle information
    img = cv2.imread(path)
    dim = (1200,1900)
    img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 13, 1)
    # ret,thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU)
    # cv2.imwrite('thresh.png', thresh)

    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    sortedCountours = sorted(contours, key=cmp_to_key(contour_sort))
    filteredCountours = []
    boxError = 10
    for cnt in sortedCountours:
        x, y, w, h = cv2.boundingRect(cnt)
        if cv2.contourArea(cnt)>15000 and h-w>0+boxError:
            filteredCountours.append(cnt)
    return img, filteredCountours

def process_contours(img, filteredCountours):
    data = []
    empty_count = 0
    empty_limit = 2
    for cnt in filteredCountours:
        x, y, w, h = cv2.boundingRect(cnt)
        ROI = img[y:y+h, x:x+w]
        #Resize
        scale = 2
        width = int(ROI.shape[1] * scale)
        height = int(ROI.shape[0] * scale)
        dim = (width, height)
        ROI = cv2.resize(ROI, dim, interpolation = cv2.INTER_AREA)

        # Get Color
        average_color_row = np.average(ROI, axis=0)
        average_color = np.average(average_color_row, axis=0)

        # Get Letter
        grayROI = cv2.cvtColor(ROI, cv2.COLOR_BGR2GRAY)
        ret,threshROI = cv2.threshold(grayROI, 0, 255, cv2.THRESH_OTSU)
        invert = np.invert(threshROI)

        # Need to make this async somehow
        temp_file = 'temp.png'
        cv2.imwrite(temp_file, invert)
        letter = read_image(temp_file)
        os.remove(temp_file)
        print(letter)
        if len(letter)>0:
            data.append((average_color, letter, x))
        else:
            empty_count+=1
            if empty_count > empty_limit:
                break
    return data

def solve_wordle(data):
    # Get true position key
    positions = list(set(pos[2] for pos in data))
    positions.sort()
    pMap = {}
    for i,p in enumerate(positions):
        pMap[p] = i

    # Process data into letters w position and categories 
    correct = []
    exists = []
    incorrect = []
    error = 10
    for line in data:
        color = line[0]
        letData = (line[1], pMap[line[2]])
        if abs(color[0]-color[1])<error and abs(color[2]-color[1])<error:
            incorrect.append(letData)
        elif color[0] < color[1] and color[2]<color[1]:
            correct.append(letData)
        else:
            exists.append(letData)

    # Open wordbank
    with open("words.txt", "r") as dict:
        words = dict.readlines()
    solutions = [word.strip().upper() for word in words]

    # Filter impossible words
    correctPass = []
    if len(correct) == 0:
        correctPass = solutions
    else:
        for word in solutions:
            possible = True
            for letter in correct:
                if not word[letter[1]] == letter[0]:
                        possible = False
                if possible:
                    correctPass.append(word)

    existsPass = []
    if len(exists) == 0:
        existsPass = correctPass
    else:
        for word in correctPass:
            possible = True
            for letter in exists:
                if not letter[0] in word or  word[letter[1]] == letter[0]:
                    possible = False
            if possible:
                existsPass.append(word)

    finalPass = []
    if len(incorrect) == 0:
        finalPass = existsPass
    else:
        for word in existsPass:
            possible = True
            for letter in incorrect:
                if  letter[0] in word:
                    possible = False
            if possible:
                finalPass.append(word)


    # Print up to 5 best guesses
    guesses = sorted(finalPass, key = cmp_to_key(compare))
    # print(len(guesses))
    text = 'Top Guesses:'
    num_guesses = 4
    for i, word in enumerate(guesses):
        if i > num_guesses:
            break
        text+="\n" + word
    return text

def final_action(image):
    img, contours = process_image(image)
    data = process_contours(img, contours)
    cv2.drawContours(img, contours, -1, (0,255,0), 3)
    cv2.imwrite('test.png', img)
    return solve_wordle(data)

# img, contours = process_image('wordle.png')
# print(len(contours))

print(final_action('wordle2.png'))