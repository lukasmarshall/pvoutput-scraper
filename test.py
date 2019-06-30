from run import getIntradayData
from pendulum import DateTime

testDate = DateTime(2019, 6, 29)
siteId = '42529'
data = getIntradayData(testDate, siteId)
print(data.headers)
print([(p.Time, p.EnergyIn) for p in data.data])