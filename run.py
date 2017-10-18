import requests
import re
import pendulum
import json

pendulum.set_formatter('alternative')

def getInputOutput(requestedDate, id, sid):
        
    requestedDate = pendulum.create(2017,10,17)
    # Weirdly, to get a day's data, you request the next day in the API. 
    # Yep.
    dateString = requestedDate.add(days=1).format('YYYYMMDD')
    r = requests.get('https://pvoutput.org/intraday.jsp?id='+id+'&sid='+sid+'&dt='+dateString+'&gs=0&m=0')
    print r.content

    # Grab the times js string. 
    times = re.search(r'var cats =(.*);',r.content,re.M|re.I).group(1)
    # Replace JS syntax so that we have only values.
    times = times.replace(' ','').replace('[','').replace(']','').replace("'","").split(',')
    # Convert each time to a pendulum object
    times = [pendulum.parse(requestedDate.to_date_string() + " "+time) for time in times]


    # Grab the energy import js string. 
    energyExport = re.search(r'var dataEnergyOut =(.*);',r.content,re.M|re.I).group(1)
    # Replace JS syntax so that we just have the values. 
    energyExport = energyExport.replace(' ','').replace('[','').replace(']','').replace("'","").split(',')
    # Convert all to floats
    energyExport = [float(x) if x != 'null' else 0.0 for x in energyExport]
    # Go backwards through the list and convert to non-cumulative by subtracting previous.
    for i in range(len(energyExport))[::-1]:
        if i > 0:
            energyExport[i] = energyExport[i] - energyExport[i - 1]

   

    # Grab the energy import js string. 
    energyImport = re.search(r'var dataEnergyIn =(.*);',r.content,re.M|re.I).group(1)
    # Replace JS syntax so that we just have the values. 
    energyImport = energyImport.replace(' ','').replace('[','').replace(']','').replace("'","").split(',')
    # Convert all to floats
    energyImport = [float(x) if x != 'null' else 0.0 for x in energyImport]
    # Go backwards through the list and convert to non-cumulative by subtracting previous. 
    for i in range(len(energyImport))[::-1]:
        if i > 0:
            energyImport[i] = energyImport[i] - energyImport[i - 1]

    # Assemble output
    output = {}
    for i in range(len(times)):
        output[str(times[i])] = {'energyExport':energyExport[i], 'energyImport':energyImport[i]}
    return output

print getInputOutput(pendulum.create(2017,10,17), '34368', '31482')

