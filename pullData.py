import requests
import zipfile
import json
import io, os, csv
import sys
import time
import pandas as pd
from datetime import datetime as dt


# Setting user Parameters

class GetQualtricsData():

    def __init__(self, surveyID, apiToken):
        self.surveyID = surveyID
        self.apiToken = apiToken
        self.path = r"C:\Users\JefferyMcCain\OneDrive - Databrains\Documents\Consulting\Athlete View\DataDumps\v2Surveys"
        self.date = dt.utcnow().strftime("%Y_%m_%dT%H.%M")

    def downloadSurvey(self):
        print('Downloading Survey: ' + self.surveyID)
        fileFormat = "csv"
        dataCenter = 'az1'
        # fileName = surveyID +
        # Setting static parameters
        requestCheckProgress = 0.0
        progressStatus = "inProgress"
        baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}/export-responses/".format(dataCenter, self.surveyID)
        headers = {
            "content-type": "application/json",
            "x-api-token": self.apiToken,
            }

        # Step 1: Creating Data Export
        downloadRequestUrl = baseUrl
        downloadRequestPayload = '{"format":"' + fileFormat + '"}'
        downloadRequestResponse = requests.request("POST", downloadRequestUrl, data=downloadRequestPayload, headers=headers)
        requestStatusCode = downloadRequestResponse.status_code
        print(requestStatusCode)
        if requestStatusCode == 200:
            progressId = downloadRequestResponse.json()["result"]["progressId"]

            # Step 2: Checking on Data Export Progress and waiting until export is ready
            while progressStatus != "complete" and progressStatus != "failed":
                print("progressStatus=", progressStatus)
                requestCheckUrl = baseUrl + progressId
                requestCheckResponse = requests.request("GET", requestCheckUrl, headers=headers)
                requestCheckProgress = requestCheckResponse.json()["result"]["percentComplete"]
                print("Download is " + str(requestCheckProgress) + " complete")
                progressStatus = requestCheckResponse.json()["result"]["status"]
                time.sleep(5)

            #step 2.1: Check for error
            if progressStatus is "failed":
                raise Exception("export failed")

            fileId = requestCheckResponse.json()["result"]["fileId"]

            # Step 3: Downloading file
            requestDownloadUrl = baseUrl + fileId + '/file'
            requestDownload = requests.request("GET", requestDownloadUrl, headers=headers, stream=True)

            # Step 4: Unzipping the file
            file = zipfile.ZipFile(io.BytesIO(requestDownload.content)).extractall(path=self.path + '//Surveys')
            print('Completed Running')
            return 'Completed'
        else:
            print(downloadRequestResponse.content)
            return 'Failed'

    def switchCSVtoPipe(self):
        print('Converting  CSV' +  self.surveyID + 'to |')
        path = self.path
        pivotQuestions = self.buildPivotList()
        if pivotQuestions['status'] == 'complete':
            embeddedList = pivotQuestions['embedded']
            QuestionstoLeave = pivotQuestions['pivot']
            surveyName = pivotQuestions['surveyName']
            """Set up Files to Read and Write Results"""
            embededDataFileName = path + '\\' + 'EmbeddedSurveyResults_' + self.surveyID + self.date + '.txt'
            """This line could pose problems for finding the correct File"""
            filename = os.listdir(path)[0]
            inputFile = path + '\\Surveys' + '\\' + surveyName + '.csv'
            print(inputFile)
            csvFile = open(inputFile, 'r', encoding='utf8')
            pivotReader = csv.DictReader(csvFile)
            rowCount = 1
            outputfile = path + '\\' + 'PivotedSurveyResults_' + self.surveyID + self.date + '.txt'
            csvOutput = open(outputfile, 'a', encoding='utf-8')
            writer = csv.writer(csvOutput, delimiter="|")
            header = ['ResponseID', 'Question', 'Answer', 'SurveyID']
            writer.writerow(header)
            """***************************************************************
            Write Results to files above
            *****************************************************************"""
            for row in pivotReader:
                try:
                    responseID = row['ResponseId']
                except KeyError:
                        responseID = row['ResponseID']

                rowCount = rowCount + 1
                for item in row:
                    listOfItems = [rowCount, responseID, item, row[item], self.surveyID]
                    if listOfItems[0] > 3:
                        if listOfItems[3] != "":
                            surveyResults = listOfItems[1:]
                            if surveyResults[1] in QuestionstoLeave:
                                writer.writerow(surveyResults)
        embeddedData = pd.read_csv(inputFile, usecols=embeddedList, skiprows=(1, 2), dtype=object)
        ed = embeddedData.assign(SurveyID=self.surveyID)
        embededDataFile = pd.DataFrame.to_csv(ed, embededDataFileName, sep="|", index=False)
        csvFile.close()
        csvOutput.close()


    def buildPivotList(self):
        print('Building Pivot & Embedded List')
        url ="https://az1.qualtrics.com/API/v3/surveys/" + self.surveyID

        headers = {
            "x-api-token": self.apiToken,
        }
        response = requests.get(url, headers=headers)
        """
        Setting up Dictionaries and lists to be returned to the data parser
        This allows us to check on the status of this Build Pivot List and shut down the application if this errors for
        any reason 
        """
        lists= {}
        pivotQuestions = []
        embedFields = []
        if response.status_code == 200:
            try:
                data = response.json()
                questions = data['result']['questions']
                embedded = data['result']['embeddedData']
                name = str(data['result']['name'])
                lists.update({'surveyName': name})
                """
                Set Up the List of Questions to be added to the embedded fields data list
                Some questions that are not in the embedded data list need to be added for filtering purposes
                This block of code does that
                """
                skipList = ['StartDate', 'EndDate', 'Status', 'RecordedDate', 'ResponseId', 'LocationLatitude',
                            'LocationLongitude', 'DistributionChannel', 'Duration (in seconds)',
                            'Finished', 'RecipientFirstName', 'RecipientLastName']
                if 'SA Core Survey from Parent Survey' in name:
                    questionsToAdd = ['Q11', 'Q12', 'Q13', 'Q14', 'Q220', 'Q221', 'Q222', 'Q223', 'Q224', 'Q225', 'Q226',
                                      'Q227', 'Q5', 'Q550', 'Q7', 'Q8']
                    skipList.extend(questionsToAdd)
                embedFields.extend(skipList)
                for question in questions:
                    qName = questions[question]['questionName']
                    qDes = questions[question]['questionText']
                    qType = questions[question]['questionType']['selector']
                    if qType in ['MAVR', 'MACOL', 'NPS', 'Likert', 'DL', 'SAVR']:
                        pivotQuestions.append(qName)

                lists.update({'pivot': pivotQuestions})

                for item in embedded:
                    name = item['name']
                    embedFields.append(name)
                lists.update({'embedded': embedFields})
                lists.update({'status': 'complete'})
                return lists
            except:
                lists.update({'status': 'failed'})
        else:
            lists.update({'status': 'failed'})


    def buildTextualMap(self):
        print('Building Textual Map')
        baseUrl = "https://az1.qualtrics.com/API/v3/surveys/" + self.surveyID
        headers = { "x-api-token": self.apiToken}
        response = requests.get(baseUrl, headers=headers)
        if response.status_code == 200:
            data = response.json()
            surveyName = data['result']['name']

            mapFileName = self.path + '\\' + 'TextualMap_' + self.surveyID + self.date + '.txt'
            csvHeader = ['QuestionID', 'QuestionName', 'NumericAnswer', 'TextualAnswer', 'Question Type', 'SurveyID']
            writer = csv.writer(open(mapFileName, 'a', encoding='utf8'), delimiter="|")
            writer.writerow(csvHeader)
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
                        mappedValues = [QID, qDescription, 1, 'True', qType, self.surveyID]

                        print(mappedValues)
                        writer.writerow(mappedValues)
                        # mappedValues = [QID, qName, 0, 'False']
                        # print(mappedValues)
                        # QID = question
                        # writer.writerow(mappedValues)
                #
                elif qType == 'MACOL':
                    choices = questions[question]['choices']
                    for choice in choices:
                        QID = str(question) + '_' + choice
                        description = choices[choice]['description']
                        # description = choice['description']
                        if qName in ['Q90', 'Q137', 'Q622']:
                            description = ' (' + description + ')'
                            qDescription = qName + description
                            if len(qDescription) > 85:
                                qDescriptionFormat = qDescription[:81]
                                qDescription = qDescriptionFormat + '...)'
                            mappedValues = [QID, qDescription, 1, 'True', qType]
                        else:
                            mappedValues = [QID, qName + '_' + choice, 1, 'True', self.surveyID]
                        print(mappedValues)
                        writer.writerow(mappedValues)
                        # mappedValues = [QID, qName, 0, 'False']
                        # print(mappedValues)
                        # QID = question
                        # writer.writerow(mappedValues)

                #
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
                        mappedValues = [QID, qName + '_NPS_GROUP', choice, npsScore, qType, self.surveyID]
                        print(mappedValues)
                        writer.writerow(mappedValues)
                        QID = question

                elif qType == "Likert":
                    choices = questions[question]['choices']
                    subQuestions = questions[question]['subQuestions']
                    for subQuestion in subQuestions:
                        for choice in choices:
                            choiceNum = choices[choice]['recode']
                            choiceText = choices[choice]['choiceText']
                            mappedValues = [question + '_' + subQuestion, qName + '_' + subQuestion, choiceNum, choiceText,
                                            qType, self.surveyID]
                            print(mappedValues)
                            writer.writerow(mappedValues)

                elif qType == "DL":
                    choices = questions[question]['choices']
                    for choice in choices:
                        choiceNum = choices[choice]['recode']
                        choiceText = choices[choice]['choiceText']
                        mappedValues = [question, qName, choiceNum, choiceText, qType, self.surveyID]
                        print(mappedValues)
                        writer.writerow(mappedValues)

                elif qType == "SAVR":
                    choices = questions[question]['choices']
                    for choice in choices:
                        choiceNum = choices[choice]['recode']
                        choiceText = choices[choice]['choiceText']
                        mappedValues = [question, qName, choiceNum, choiceText, qType, self.surveyID]
                        print(mappedValues)
                        writer.writerow(mappedValues)
    def getSurveyResults(self):
        getData = self.downloadSurvey()
        if getData == 'Completed':
            self.switchCSVtoPipe()




