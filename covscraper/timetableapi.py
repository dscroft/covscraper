import requests
from covscraper import auth
from bs4 import BeautifulSoup
import datetime, sys, re
import json
import urllib

WEEKOFFSET = { "2016-2017": datetime.date(2016,7,17), \
               "2017-2018": datetime.date(2017,7,16), \
               "2018-2019": datetime.date(2018,7,15), \
               "2019-2020": datetime.date(2019,7,14), \
               "CU20_21": datetime.date(2020,7,5), \
               "CU21_22": datetime.date(2021,7,4), \
               "CU22_23": datetime.date(2022,7,3), \
               "CU23_24": datetime.date(2023,9,4) }

def get_lecturer_timetable( session, date=datetime.datetime.now() ):
    """get the sessions timetabled for the person used to authenticate the current session"""
    url = "https://webapp.coventry.ac.uk/Timetable-main/Timetable/Lecturer#year={year}&month={month}&day={day}&view=agendaWeek"

    response = session.get(url.format(year=date.year, month=date.month, day=date.day))

    return _decode_timetables( response.text )

def get_timetable( session, module="", room="", course="", uid="", lecturer="", stage="", date=datetime.datetime.now() ):
    """get the sessions timetabled for a given module, room, student uid, course or any combination thereof"""
    url = "https://webapp.coventry.ac.uk/Timetable-main/Timetable/Search?CourseId={course}&ModuleId={module}&RoomId={room}&queryStudent={uid}&studentId={uid}&viewtype=%2F&searchsetid={academicyear}&queryModule={module}&queryLecturer={lecturer}&queryRoom={room}&queryCourse={course}&Stg={stage}&timetabletype=normal"

    academicyear = academic_year(date)

    url = url.format(module=auth.url_safe(module), 
        room=auth.url_safe(room), 
        course=auth.url_safe(course), 
        lecturer=auth.url_safe(lecturer), 
        uid=uid, stage=stage, 
        academicyear=academicyear)

    #print( url )

    response = session.get(url)

    return _decode_timetables( response.text )


def get_register( session, slot ):
    """get the register for a timetabled slot"""
    if "dummyUrl" in slot:
        url = "https://webapp.coventry.ac.uk" + slot["dummyUrl"]
    else:
        url = "https://webapp.coventry.ac.uk/Timetable-main/Attendance?SetId={academicyear}&SlotId={eventid}&WeekNumber={week}"
        url = url.format(academicyear=academic_year(slot["start"]), \
                         eventid=slot["ourEventId"], \
                         week=cov_week(slot["start"]) )
    
    #print( url )

    response = session.get(url)
    slot["register"] = _decode_register(response.text)
    
    return slot


def academic_year( date ):
    """which academic year is a given date, takes a datetime.date or timetabled slot, returns a string"""
    if isinstance(date,dict) and "start" in date:
        date = date["start"]

    if isinstance(date,datetime.datetime):
        date = date.date()

    orderedDates = sorted( list(WEEKOFFSET.items()), key=lambda x: x[1], reverse=True )

    for n, d in orderedDates:
        if date >= d:
            return n

    return None    


def cov_week( date ):
    """which academic week is a given date, takes a datetime.date or timetabled slot, returns an int"""
    if isinstance(date,dict) and "start" in date:
        date = date["start"]

    if isinstance(date,datetime.datetime):
        date = date.date()

    return (date - WEEKOFFSET[academic_year(date)]).days//7


def _decode_timetables( html ):
    """extract session information from timetable html page, returns list of dictionaries"""
    sessionReg = re.compile(r"{[^}]*ourEventId[^}]*}", re.MULTILINE|re.DOTALL)
    commentReg = re.compile(r"\s*//.*", re.MULTILINE)
    quoteReg = re.compile( r"(^\"[^\"]*\":\s*\".*)(\")(.*\"[,\r\n])", re.MULTILINE ) 
    dateReg = re.compile(r"new Date\((.*)\)", re.MULTILINE)
    propReg = re.compile(r"(\w*)(:)", re.MULTILINE)
    damnCharReg = re.compile(r"&#[0-9]{1,};")
    
    slots = []

    for match in sessionReg.findall(html):
        match = commentReg.sub("",match)
        match = dateReg.sub(r'"\1"',match)
        match = propReg.sub(r'"\1"\2',match)
        match = match.replace("'", '"')
        
        # what complete bastard puts unescaped quotes in a string?
        while quoteReg.search(match):
            match = quoteReg.sub(r"\1\3", match)
        
        # ffs, tabs?        
        match = match.replace( "\t", "" )

        j = json.loads(match)

        # decode dates
        for f in ["start","end"]:
            if f in j:
                d = [int(i) for i in j[f].split(",")]
                d[1] += 1 # webtimetable has jan as month 0
                d = datetime.datetime(*d)

                j[f] = d

        # split lecturers
        for f in ["lecturer"]:
            if f in j:
                j[f] = j[f].split("; ")
                if j[f] == ['']:
                    j[f] = []
                j[f] = set(j[f])

        slots.append(j)
        
        slots = sorted(slots, key=lambda x: x["start"])

    return slots


def _decode_register( html ):
    """extract register information from register html page, returns list of tuples"""
    soup = BeautifulSoup( html, "lxml" )

    students = []
    try:
        for tr in soup.findAll("tr")[1:]:
            student = [td.text for td in tr.findAll("td")][:4]
            student[1] = int(student[1])
            if student[3] == "": student[3] = None
            students.append(tuple(student))
    except IndexError:
        pass
        
    return students

