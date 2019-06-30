from run import getIntradayData, getSession, closeSession
from pendulum import DateTime
import csv
from pathlib import Path

siteId = '40873'

directory = Path('directory'+siteId)
if not directory.exists():
    directory.mkdir()

# if not logged in then this will only work for th last 14 days
testDate = DateTime(2019, 2, 1)

sesh = getSession('username', 'password')

for idx in range(1,130):
    dateString = testDate.to_date_string()
    print('creating file ', dateString)
    data = getIntradayData(testDate, siteId, sesh)
    with open(directory.as_posix() + f'/{dateString}.csv','w', newline='') as csvFile:
        dataFile = csv.writer(csvFile)
        dataFile.writerow(data.headers)
        dataFile.writerows(data.data)

    testDate = testDate.add(days=1)

sesh.close()
