import requests
from covscraper import auth
import csv, io, re
from bs4 import BeautifulSoup

def student_ids( session, module ):
  return tuple(get_grades( session, module ).keys())

def _decode_grades( csvstr ):  
    headers = {"Email address":"email",
               "First name":"forename",
               "Surname":"surname",
               "ID number":None,
               "Course Codes":"course",
               "Institution":None,
               "Last downloaded from this course":None,
               "User Type":None,
               "Suspended":None,
               "Department":None,
               "Faculty":None}

    rawdata = list(csv.reader( io.StringIO( csvstr ) ))
    header, rawdata = rawdata[0], rawdata[1:]

    uidpos = header.index("ID number")
    marks = {}
    for row in rawdata:
        if row[uidpos]=='': continue
        uid = int(row[uidpos])
        details = { headers[k]:v for k, v in zip(header,row) if headers.get(k,None) }
        details["grades"] = [ (k,None if v=='-' else float(v)) for k, v in zip(header,row) if k not in headers ]
        marks[uid] = details

    return marks
    
  
def get_grades( session, module ):
    """get the sessions timetabled for the person used to authenticate the current session"""
    # get session key    
    url = "https://cumoodle.coventry.ac.uk/grade/report/grader/index.php?id={module}"
    response = session.get( url.format(module=module) )

    keyRegex = re.compile( r"\"sesskey\":\"([^\"]*)\"" )
    sesskey = keyRegex.search( response.text ).group(1)

    #print( response.text )

    soup = BeautifulSoup( response.text, "lxml" )
    items = [ int(e["data-itemid"]) for e in soup.findAll("th") if e.has_attr("data-itemid") ]

    # get grades
    url = "https://cumoodle.coventry.ac.uk/grade/export/txt/export.php"
    data = {"id":module,
        "sesskey":sesskey,
        "display[letter]":0,
        "display[real]":1,
        "display[percentage]":0,
        "_qf__grade_export_form":1}
    data.update({ "itemids[{}]".format(i):1 for i in items })
    response = session.post( url, data=data )

    return _decode_grades( response.text )

