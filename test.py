from run import PVOutput
from pendulum import DateTime
import csv
from pathlib import Path

siteId = '57775'

directory = Path('directory'+siteId)
if not directory.exists():
    directory.mkdir()

# if not logged in then this will only work for th last 14 days
testDate = DateTime(2019, 2, 1)

pvo = PVOutput()
pvo.login('username', 'password')

for idx in range(1,140):
    dateString = testDate.to_date_string()
    print('creating file ', dateString)
    try:
        data = pvo.getIntradayData(testDate, siteId)
    except NameError as e:
        print(e)
        print("missing data for " + dateString)
        testDate = testDate.add(days=1)
        continue

    with open(directory.as_posix() + f'/{dateString}.csv','w', newline='') as csvFile:
        dataFile = csv.writer(csvFile)
        dataFile.writerow(data.headers)
        dataFile.writerows(data.data)

    testDate = testDate.add(days=1)