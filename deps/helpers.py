import csv
from datetime import datetime as dt

reportDate = dt.utcnow().strftime('%d.%m.%y %H.%M.%S')


class Helpers:
    def csvToPipe(self, inputFile, outputFile):
        # inputFile = r'fileName'
        # outputFile = r'fileName' + reportDate + '.txt'
        with open(inputFile, encoding="utf8") as fileIn:
            with open(outputFile, 'w', newline='', encoding="utf8") as fileOut:
                reader = csv.DictReader(fileIn, delimiter=",")
                writer = csv.DictWriter(fileOut, reader.fieldnames, delimiter="|")
                writer.writeheader()
                writer.writerows(reader)
                print('File Converted')
                return 'Complete'

