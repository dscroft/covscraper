#from timetableapi import *
from covscraper import *
import pytz
import datetime
import getpass
import ics

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
	
	session = auth.Authenticator(input("username: "), getpass.getpass("password: "))
	slots = timetableapi.get_lecturer_timetable(session)

	cal = ics.Calendar()
	with open("timetable.ics", "w") as f:
		f.write(header)
		
		for c, s in enumerate(slots):
			if s["title"] == "": continue
			if timetableapi.cov_week(s) <= 5 or s["start"].year > 2017: continue

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
	

		
		
		
		
		
		
		
		
		
		
		
		
		