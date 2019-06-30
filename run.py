import requests
import re
import pendulum
import json
from collections import namedtuple
from time import sleep, time

IntradayData = namedtuple('IntradayData', 'headers data')
DataPoint = namedtuple('DataPoint', ['Time', 'EnergyOut', 'PowerOut', 'PowerAvg', 'EnergyIn', 'EnergyNet', 'PowerIn', 'Export', 'Import', 'Volt'])

_host = 'https://pvoutput.org'


class PVOutput:

    def __init__(self):
        self.request_delay = 2 # seconds delay between requests
        self.last_request_time = time()


    def login(self, username: str, password: str):
        s = requests.Session()
        s.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Host': 'pvoutput.org',
            'Referer': 'https://pvoutput.org/ladder.jsp' 
        })
        r = s.post(f'{_host}/index.jsp', {'login': username, 'password': password})
        if 'logout' not in str(r.content):
            # may be due to captcha
            print("Login was unsuccessful", r.status_code, r.content)
            s.close()

        self.session = s

        self._delay()
        s.get(f'{_host}/ladder.jsp')

    def _closeSession(self):
        self.session.get(f'{_host}/logout.jsp')
        self.session.close()
        del self.session
    
    def _delay(self):
        time_diff = time() - self.last_request_time 
        self.last_request_time = time()
        if time_diff < self.request_delay:
            sleep(self.request_delay - time_diff)

    def _getIntradayPage(self, requestedDate: pendulum.DateTime, siteId: str):
        # Weirdly, to get a day's data, you request the next day in the API... Yep
        dateString = requestedDate.add(days=1).format('YYYYMMDD')
        url = f'{_host}/intraday.jsp?id=&sid={siteId}&dt={dateString}&gs=0&m=0'
        # self._delay()
        if not self.session:
            r = requests.get(url)
        else:
            r = self.session.get(url)
        
        return r

    def getIntradayData(self, requestedDate: pendulum.DateTime, siteId: str):

        r = self._getIntradayPage(requestedDate, siteId)

        if 'timeArray' not in str(r.content):
            print("Page content is incorrect, please check the page.")
            action = input('Try again? (Y/N)')
            if action.lower() == 'y':
                r = self._getIntradayPage(requestedDate, siteId)
            else:
                exit()

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

    def __del__(self):
        if hasattr(self, 'session'):
            self._closeSession()

