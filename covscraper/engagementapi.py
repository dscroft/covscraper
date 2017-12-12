import requests
from bs4 import BeautifulSoup
import datetime, sys, re
import dateutil.parser
from covscraper import auth

def get_student_engagement( session, uid ):
    url = "https://engagementdashboard.coventry.ac.uk/attendance/all?id={uid}"

    response = session.get(url.format(uid=uid))

    return _decode_engagement( response.text )


def get_attendance( slots ):
    absolute = { "ontime": 0, "late": 0, "unverified": 0 }
    for s in slots:
        absolute[s["type"]] = absolute.get(s["type"],0)+1
    absolute["future"] = absolute.get("",0)
    if "" in absolute: del absolute[""]
        
    total = sum([ v for k, v in absolute.items() if k != "future"])
    percent = {"confirmed": 0, "possible": 0, "late": 0}
    
    if total == 0: return absolute, percent
    
    percent["confirmed"] = absolute["ontime"]
    percent["late"]      = absolute["ontime"] + absolute["late"]
    percent["possible"]  = absolute["ontime"] + absolute["late"] + absolute["future"]
    
    percent = { k: v/total*100 for k, v in percent.items() }
        
    return absolute, percent

def _decode_engagement( html ):
    gaugeReg = re.compile( r'var\s{1,}gauge([0-9])\s{1,}=\s{1,}loadLiquidFillGauge\(\s*"fillgauge[0-9]"\s*,\s*([0-9]{1,3})\s*\);' )
    slotReg = re.compile( r'{[^}]*id[^}]*module[^}]*}' )
    fieldReg = re.compile( r"([a-zA-Z]{1,}):\s([0-9]{1,}|'[^']*')" )

    # get gauge values
    gauges = {}
    for num, val in gaugeReg.findall( html ):
        gauges[int(num)] = int(val)
        
    try:
        gauges = {"period": gauges[1], "semester": gauges[2], "overall": gauges[3]}
    except KeyError:
        raise ValueError("Student does not exist on engagementdashboard.")
    
    # get slots
    slots = []
    
    fieldsOfInterest = {"title":"title", "startTime":"start", "finishTime":"end", "type":"type", "location":"room", "module":"module", "teach":"teach"}
    for slot in slotReg.findall( html ):

        ##ields = {fieldsOfInterest[key]: val.replace("'", "") for key, val in fieldReg.findall( slot ) if key in fieldsOfInterest}
        fields = {key: val.replace("'", "") for key, val in fieldReg.findall( slot )}
    
        for field in ("start",):
            fields[field] = dateutil.parser.parse( fields[field] )
    
        slots.append(fields)
            
    return gauges, slots
    
if __name__ == "__main__":
    with open("test.html") as f:
        html = f.read()
        
        gauges, slots = _decode_engagement( html )
        print(gauges)
    
    

    
    
    
    
    
   