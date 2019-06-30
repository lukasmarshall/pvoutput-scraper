import requests
import re
import pendulum
import json
from collections import namedtuple

IntradayData = namedtuple('IntradayData', 'headers data')
DataPoint = namedtuple('DataPoint', ['Time', 'EnergyOut', 'PowerOut', 'PowerAvg', 'EnergyIn', 'EnergyNet', 'PowerIn', 'Export', 'Import', 'Volt'])

_host = 'https://pvoutput.org'

def getSession(username: str, password: str):
    s = requests.Session()
    r = s.post(f'{_host}/index.jsp', {'login': username, 'password': password})
    if r.status_code != 302:
        print("Login was unsuccessful")
        s.close()

    return s

def closeSession(session):
    s.get(f'{_host}/logout.jsp')
    s.close()

def getIntradayData(requestedDate: pendulum.DateTime, siteId: str, session=None):

    # Weirdly, to get a day's data, you request the next day in the API... Yep
    dateString = requestedDate.add(days=1).format('YYYYMMDD')
    url = f'{_host}/intraday.jsp?id=&sid={siteId}&dt={dateString}&gs=0&m=0'
    if not session:
        r = requests.get(url)
    else:
        r = session.get(url)

    # list of variable names in js script we want
    varNames = ('dataEnergyOut', 'dataPowerOut', 'dataPowerAvg', 'dataEnergyIn',
        'dataEnergyNet', 'dataPowerIn', 'dataExport', 'dataImport', 'dataVolt')
    dataPoints = 0
    data = {}

    # Grab the times js string. 
    for match in re.finditer(r'var (\w+) = \[(.*?)\];', str(r.content), re.M|re.I):
        varName, dataString = match.group(1, 2)
        if (varName in varNames or varName == 'timeArray') and dataString:
            dataList = dataString.split(',')
            if len(dataList) > 0:
                data[varName] = dataList
            
            if len(dataList) > dataPoints:
                dataPoints = len(dataList)

    if 'timeArray' not in data:
        raise NameError('timeArray is missing from page, this program may be out of date.')

    for varName in varNames:
        if varName not in data:
            data[varName] = [0 for x in range(0, dataPoints)]
    
    dataList = []

    # Convert each time to a pendulum object
    for idx, val in enumerate(data['timeArray']):
        hour = int(val) // 60; minute = int(val) % 60
        dataPoint = [requestedDate.set(hour=hour,minute=minute)]
        for varName in varNames:
            dataPoint.append(float(data[varName][idx]) if data[varName][idx] != 'null' else None)

        dataList.append(DataPoint(*dataPoint))

    headers = ('Time', 'Energy Out', 'Power Out', 'Power Avg', 'Energy In', 'Energy Net', 'Power In', 'Export', 'Import', 'Volt')

    return IntradayData(headers, dataList)
