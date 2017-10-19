from timetableapi import *
import pytz

icsTemplate = """BEGIN:VEVENT
CLASS:PUBLIC
DTSTART:{start}
DTEND:{end}
LOCATION:{room}
PRIORITY:5
SEQUENCE:0
SUMMARY:LANGUAGE=en-gb:{title}
TRANSP:OPAQUE
STATUS:CONFIRMED
UID:{eventid}-{counter}@icsgen.org
X-MICROSOFT-CDO-BUSYSTATUS:BUSY
X-MICROSOFT-CDO-IMPORTANCE:1
BEGIN:VALARM
TRIGGER:-PT5M
ACTION:DISPLAY
DESCRIPTION:Reminder
END:VALARM
END:VEVENT"""

if __name__ == "__main__":
	session = authenticate_session("", "")
	timezone = pytz.timezone("Europe/London")

	slots = get_lecturer_timetable(session)

	with open("timetable.ics", "w") as f:
		for c, s in enumerate(slots):
			if s["title"] == "": continue
			if cov_week(s) <= 20 or s["start"].year > 2017: continue

			for attr in ("start","end"):
				s[attr] = timezone.localize(s[attr])

	

			ics = icsTemplate.format(title=s["title"], \
									 counter=c, \
									 start=s["start"].isoformat(), \
									 end=s["end"].isoformat(), \
									 eventid=s["ourEventId"], \
									 room=s["room"] )
			
			print( ics, file=f )

	

			
	#with open("timetable.ics", "w") as f:
		#f.writelines(calendar)