# exported from the timetable website to a calendar file (ics)

#from timetableapi import *
from covscraper import *
import pytz
import datetime
import getpass
import ics, getopt, sys

header = """BEGIN:VCALENDAR
VERSION:2.0
"""

footer = """END:VCALENDAR
"""

event = """BEGIN:VEVENT
DTSTAMP:{now:%Y%m%dT%H%M%SZ}
DTSTART:{start:%Y%m%dT%H%M%SZ}
DTEND:{end:%Y%m%dT%H%M%SZ}
SUMMARY:{title}
LOCATION:{room}
UID:{eventid}-{week}@coventry.ac.uk
CLASS:PUBLIC
PRIORITY:5
TRANSP:OPAQUE
STATUS:CONFIRMED
SEQUENCE:0
X-MICROSOFT-CDO-APPT-SEQUENCE:0
X-MICROSOFT-CDO-BUSYSTATUS:BUSY
X-MICROSOFT-CDO-INTENDEDSTATUS:BUSY
X-MICROSOFT-CDO-ALLDAYEVENT:FALSE
X-MICROSOFT-CDO-IMPORTANCE:1
X-MICROSOFT-CDO-INSTTYPE:0
X-MICROSOFT-DISALLOW-COUNTER:FALSE
BEGIN:VALARM
TRIGGER:-PT5M
ACTION:DISPLAY
DESCRIPTION:Reminder
END:VALARM
END:VEVENT
"""
    
if __name__ == "__main__":
    tzCoventry = pytz.timezone("Europe/London")
    tzUtc = pytz.timezone("Etc/UTC")
    now = datetime.datetime.now()
    
    usageTxt = "help"
    
    params = {"user": None, "pass": None, "room": "", "module": "", "course": "", "date": None, "until": None, "lecturer": ""}
    week = timetableapi.cov_week(datetime.datetime.now())
        
    # configure flags
    shortopts = "".join(["{:.1}:".format(i) for i in params])
    longopts = ["help","students"]+["{}=".format(i) for i in params]
    try:
        opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    except getopt.GetoptError as e:
        print(e)
        sys.exit(1)
        
    # process flags
    for o, a in opts:
        if o in ("-h", "--help"):
            print(usageText)
            sys.exit(1)
        
        for p in params:
            if o in ("-{:.1}".format(p), "--{}".format(p)):
                params[p] = a

    # handle defaults
    params["date"] = datetime.datetime.strptime(params["date"], "%d/%m/%Y") if params["date"] else datetime.datetime.now()
    if params["until"]:
        params["until"] = datetime.datetime.strptime(params["until"], "%d/%m/%Y")
      
    if not params["user"]: params["user"] = input("username: ")
    if not params["pass"]: params["pass"] = getpass.getpass("password: ")
        
    currentweek = timetableapi.cov_week(params["date"])

    # authenticate and get the timetable
    session = auth.Authenticator(params["user"], params["pass"])
    
    if params["room"] or params["module"] or params["course"] or params["lecturer"]:
        slots = timetableapi.get_timetable( session, module=params["module"], room=params["room"], course=params["course"], date=params["date"], lecturer=params["lecturer"] )
    else:
        print("lec")
        slots = timetableapi.get_lecturer_timetable(session)

    cal = ics.Calendar()
    with open("timetable.ics", "w") as f:
        f.write(header)

        for c, s in enumerate(slots):
            if s["title"] == "": continue
            if s["start"] < params["date"]: continue
            if params["until"] and s["end"] > params["until"]: continue

            for attr in ("start","end"):
                s[attr] = tzCoventry.localize(s[attr]).astimezone(tzUtc)

            e = event.format( now=now, \
                      start=s["start"], \
                      end=s["end"], \
                      title=s["title"], \
                      room=s["room"], \
                      eventid=s["ourEventId"], \
                      week=timetableapi.cov_week(s["start"]) )

            f.write(e)

        f.write(footer)


        
        
        
        
        
        
        
        
        
        
        
        
        
