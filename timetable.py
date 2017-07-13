import urllib2, re
from ntlm import HTTPNtlmAuthHandler
import json
import bs4
from bs4 import BeautifulSoup
import getpass, getopt, sys, datetime
import threading

def pull_auth_html( url, usr, pwd ):
    passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
    passman.add_password(None, url, usr, pwd)

    # create the NTLM authentication handler
    auth_NTLM = HTTPNtlmAuthHandler.HTTPNtlmAuthHandler(passman)
    
    # create and install the opener
    opener = urllib2.build_opener(auth_NTLM)
    urllib2.install_opener(opener)

    response = urllib2.urlopen(url)

    return response.read(), response.getcode()

def pull_timetable( usr, pwd, module, date ):
    sp = (date.year,date.year+1) if date.month>=9 else (date.year-1,date.year)
    searchPeriod = "{}-{}".format( *sp )

    module = module.upper()

    sessionPattern = re.compile( r"{[^}]*ourEventId[^}]*}", flags=re.MULTILINE+re.DOTALL )
    linePattern = re.compile( r"(ourEventId|title|start|end|room):[\s']*((new Date\([0-9,\s]*\))|([^,']*))[\s']*,", flags=re.DOTALL )

    
    baseUrl = 'https://webapp.coventry.ac.uk/'
    timetableUrl = baseUrl + 'Timetable-main/Timetable/Search?searchsetid={}&queryModule={}&timetabletype=normal&weeksordates=dates#year={}&month={}&day={}&view=agendaWeek'
    sessionUrl = 'https://webapp.coventry.ac.uk/Timetable-main/Attendance?SetId={}&SlotId={}&WeekNumber={}'

    # generate url
    url = timetableUrl.format( searchPeriod, module, date.year, date.month, date.day )
    response, code = pull_auth_html( url, usr, pwd )

    sessions = []
    for sessionMatch in sessionPattern.finditer( response ):
        session = {}

        for lineMatch in linePattern.finditer( sessionMatch.group(0) ):
            key, value = lineMatch.group(1), lineMatch.group(2)

            if key == "ourEventId":
                key = "eventId"
                value = int(value)
            elif key in ("title", "room"):
                pass
            elif key in ("start", "end"):
                year, month, day, hour, mn = [ int(i) for i in value[9:-1].split(",") ][:5]
                value = datetime.datetime( year, month+1, day, hour, mn )
                    
            session[key] = value

        if "dummyUrl" in session:
            session["url"] = baseUrl + session["dummyUrl"]
        else:
            # works for the moment but if anything is going to break this is
            weekNumber = (session["start"].isocalendar()[1] + 23) % 52
            session["url"] = sessionUrl.format( searchPeriod, session["eventId"], weekNumber )

        sessions.append( session )

    # only care about sessions in the same week
    sessions = [ i for i in sessions if i["start"].isocalendar()[1] == date.isocalendar()[1] ]

    return sessions



def pull_session_details( usr, pwd, session ):
    if "url" not in session:
        raise ValueError( "Session has no url" )

    response, code = pull_auth_html( session["url"], usr, pwd )

    students = set()

    soup = BeautifulSoup( response, "html.parser" )
    table = soup.find( "table" )
    body = table.find( "tbody" )
    for row in body.findChildren( "tr" ):
        student = tuple([ i.text for i in row.findChildren("td") ][:4])
        students.add( student )

    session["students"] = students

    return session
        



if __name__ == '__main__':
    usr = None
    pwd = None
    module = None
    date = None
    
    options, args = getopt.getopt( sys.argv[1:], 'u:p:m:d:s', ["user=", "module=", "password=", "date=", "students"] )

    for opt, arg in options:
        if opt in ('-u','--user'):
            usr = arg
        elif opt in ('-p', '--password'):
            print( "Supplying your password as an argument is NOT recommended")
            pwd = arg
        elif opt in ('-m', '--module'):
            module = arg
        elif opt in ('-d', '--date'):
            date = dateutil.parser.parse( arg, dayfirst=True )
        elif opt in ('-s'):
            print( "list" )
            liststudents = True

    if not usr:
        print "Enter username:", 
        usr = raw_input()

    if not pwd:
        pwd = getpass.getpass( "Enter password: ")

    if not module:
        print "Enter module code:",
        module = raw_input()

    if not date:
        print "Using todays date" 
        date = datetime.datetime.now()

    sessions = pull_timetable( usr, pwd, module, date )

    threads = [ threading.Thread(target=pull_session_details, args=(usr,pwd,i)) for i in sessions ]
    for thread in threads: thread.start()
    for thread in threads: thread.join()

    for session in sessions:
        print( "{:8} {:2} to {:2} - Room {:6} - {:2} students - {}".format( session["start"].strftime("%A"), \
                                                                session["start"].hour, session["end"].hour, session["room"], \
                                                                len(session["students"]), session["title"] ) )




    

    #print( soup )





