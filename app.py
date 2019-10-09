from deps.pullData import GetQualtricsData
from datetime import datetime
from time import sleep

def getSurveyIDS():
    surveyIds = []
    fileName = ''
    with open(fileName, encoding='utf8') as file:
        for item in file:
            value = item.split(',')
            surveyId = value[1].replace('\n', '')
            surveyIds.append(surveyId)
    return surveyIds

runTime = datetime.now()
apiToken = 
# surveyID =
surveyIDs =  #getSurveyIDS()



for surveyID in surveyIDs:
    q = GetQualtricsData(surveyID, apiToken)
    q.getSurveyResults()
    q.buildTextualMap()
    sleep(2)


endTime = datetime.now() - runTime
print('Time Elapsed')
print(endTime)
