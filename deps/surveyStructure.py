import json
import csv
from datetime import datetime
import requests
import os
from configparser import ConfigParser

"""Set Up Variables"""
runDate = datetime.utcnow().strftime('%Y.%m.%d.T.%H.%M.%S')
cfgFilePath = os.path.dirname(__file__) + '/qualCred.txt'
fileOutputPath = os.path.dirname(os.path.dirname(__file__)) + '/dataFiles'


"""Make Get Survey Request"""
cfg = ConfigParser()
cfg.read(cfgFilePath)
apiToken = cfg.get('qualtrics', 'apiToken')
# surveyId = cfg.get('surveys', 'saCore')
surveyIds = ['SV_5mYVInJs3YGlZyJ', 'SV_erGLgwr6XXgzI3z', 'SV_ahqKD1rsSgduRmJ', 'SV_ex2STQCUxKKI8DP',
             'SV_6rkUrZ8jku5VRiZ', 'SV_abcf21eFe7xPIm9', 'SV_7WIfl0jKSgLtpVb']
dataCenter = cfg.get('qualtrics', 'dataCenter')
userId = cfg.get('qualtrics', 'userId')

for surveyId in surveyIds:
    baseUrl = "https://" + dataCenter + ".qualtrics.com/API/v3/surveys/" + surveyId
    headers = {
        "x-api-token": apiToken,
    }
    """
    Mapping Live to API
    """
    response = requests.get(baseUrl, headers=headers)
    if response.status_code == 200:
        data = response.json()

        """
        Set Up File to be Saved
        """
        surveyName = data['result']['name']
        mapFileName = 'TextMap_' + surveyName + '_' + runDate + '.txt'
        outputFile = fileOutputPath + '/' + mapFileName
        header = ['QuestionID', 'QuestionName', 'NumericAnswer', 'TextualAnswer', 'QuestionType']
        writer = csv.writer(open(outputFile, 'a', encoding='utf8'), delimiter="|")
        writer.writerow(header)

        """
        Run through questions in survey
        """
        questions = data['result']['questions']

        for question in questions:
            qName = questions[question]['questionName']
            qDes = questions[question]['questionText']
            qType = questions[question]['questionType']['selector']

            if qType == 'MAVR':
                choices = questions[question]['choices']
                for choice in choices:
                    QID = str(question) + '_' + choice
                    description = choices[choice]['description']
                    description = ' (' + description + ')'
                    qDescription = qName + description
                    if len(qDescription) > 83:
                        qDescriptionFormat = qDescription[:81]
                        qDescription = qDescriptionFormat + '...)'
                    mappedValues = [QID, qName, 1, 'True', qType]
                    print(mappedValues)
                    writer.writerow(mappedValues)
            elif qType == 'MACOL':
                choices = questions[question]['choices']
                for choice in choices:
                    QID = str(question) + '_' + choice
                    mappedValues = [QID, qName, 1, 'True', qType]
                    print(mappedValues)
                    writer.writerow(mappedValues)
            elif qType == 'NPS':
                choices = questions[question]['choices']
                for choice in choices:
                    QID = question
                    npsValue = int(choice)
                    if npsValue >= 0 and npsValue <= 6:
                        npsScore = "Detractor"
                    elif npsValue >= 7 and npsValue <= 8:
                        npsScore = "Passive"
                    elif npsValue >= 9 and npsValue <= 10:
                        npsScore = "Promoter"
                    mappedValues = [QID, qName, choice, npsScore, qType]
                    print(mappedValues)
                    writer.writerow(mappedValues)
            elif qType == "Likert":
                choices = questions[question]['choices']
                for choice in choices:
                    choiceNum = choices[choice]['recode']
                    choiceText = choices[choice]['choiceText']
                    mappedValues = [question, qName, choiceNum, choiceText, qType]
                    print(mappedValues)
                    writer.writerow(mappedValues)
            elif qType == "DL":
                choices = questions[question]['choices']
                for choice in choices:
                    choiceNum = choices[choice]['recode']
                    choiceText = choices[choice]['choiceText']
                    mappedValues = [question, qName, choiceNum, choiceText, qType]
                    print(mappedValues)
                    writer.writerow(mappedValues)
            elif qType == "SAVR":
                choices = questions[question]['choices']
                for choice in choices:
                    choiceNum = choices[choice]['recode']
                    choiceText = choices[choice]['choiceText']
                    mappedValues = [question, qName, choiceNum, choiceText, qType]
                    print(mappedValues)
                    writer.writerow(mappedValues)


