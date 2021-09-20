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
        uid = row[uidpos]
        details = { headers[k]:v for k, v in zip(header,row) if headers.get(k,None) }
        details["grades"] = [ (k,None if v=='-' else float(v)) for k, v in zip(header,row) if k not in headers ]
        marks[uid] = details

    return marks

def student_ids( session, module ):
    return list(get_grades( session, module ).keys())
  
def get_grades( session, module ):
    """get the sessions timetabled for the person used to authenticate the current session"""
    # get session key    
    url = "https://cumoodle.coventry.ac.uk/grade/report/grader/index.php?id={module}"
    response = session.get( url.format(module=module) )

    keyRegex = re.compile( r"\"sesskey\":\"([^\"]*)\"" )
    sesskey = keyRegex.search( response.text ).group(1)

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

def get_question_bank( session, module ):
    # get the initial bank export page so we can get the category id and session keys
    url = f"https://cumoodle.coventry.ac.uk/question/edit.php?courseid={module}"
    response = session.get( url )

    soup = BeautifulSoup( response.text, "lxml" )

    # get the session key
    keyRegex = re.compile( r"\"sesskey\":\"([^\"]*)\"" )
    sesskey = keyRegex.search( response.text ).group(1)

    # get the category id
    categories = soup.find( id="id_selectacategory" )
    if categories == None: return None
    category = next( ( c["value"] \
                       for c in categories.findAll( "option" ) \
                       if c.text.startswith("Top for") ) )

    # send the post request to generate the moodle xml document
    url = f"https://cumoodle.coventry.ac.uk/question/export.php"
    data = {
        "courseid": module,
        "sesskey": sesskey,
        "_qf__question_export_form": 1,
        "mform_isexpanded_id_fileformat": 1,
        "mform_isexpanded_id_general": 1,
        "format": "xml",
        "category": category,
        "cattofile": 1,
        "contexttofile": 1,
        "submitbutton": "Export+questions+to+file" }
    response = session.post( url, data=data )

    soup = BeautifulSoup( response.text, "lxml" )
    download = soup.find( "div", {"class": ["box","generalbox"]} ).find( "a", text="click here" )
    downloadUrl = download["href"]

    # some of these are big files
    response = session.get( downloadUrl, stream=True )
    result = b''
    for chunk in response.iter_content( chunk_size=1024 ):
        result += chunk

    if response.status_code == 404: return None

    return result.decode()
    
def get_module_name( session, module ):
    if module in (0,1): return None

    url = f"https://cumoodle.coventry.ac.uk/course/view.php?id={module}"

    response = session.get( url )
    if response.status_code != 200: return None

    soup = BeautifulSoup( response.text, "lxml" )
    title = soup.find( "title" )
    return title.text