import requests
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
import datetime, sys, re
import json
import urllib

WEEKOFFSET = { "2016-2017": datetime.date(2016,7,17), \
			   "2017-2018": datetime.date(2017,7,16) }

def authenticate_session( user, password ):
	"""log into the timetable system"""
	url = "https://webapp.coventry.ac.uk/Timetable-main"
	#headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}

	session = requests.Session()
	session.auth = HttpNtlmAuth("COVENTRY\\{}".format(user), password)
	response = session.get(url)

	return session


def get_lecturer_timetable( session, date=datetime.datetime.now() ):
	"""get the sessions timetabled for the person used to authenticate the current session"""
	url = "https://webapp.coventry.ac.uk/Timetable-main/Timetable/Lecturer#year={year}&month={month}&day={day}&view=agendaWeek"

	response = session.get(url.format(year=date.year, month=date.month, day=date.day))

	return _decode_timetables( response.text )


def get_timetable( session, module="", room="", course="", date=datetime.datetime.now() ):
	"""get the sessions timetabled for a given module, room, course or any combination thereof"""
	url = "https://webapp.coventry.ac.uk/Timetable-main/Timetable/Search?CourseId={course}&ModuleId={module}&RoomId={room}&viewtype=%2F&searchsetid={academicyear}&queryModule={module}&queryRoom={room}&queryCourse={course}&timetabletype=normal"

	academicyear = academic_year(date)

	response = session.get(url.format(module=_url_safe(module), room=_url_safe(room), course=_url_safe(course), academicyear=academicyear))

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

	response = session.get(url)
	#print(url)
	register = _decode_register(response.text)
	return register


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


def _url_safe( val ):
	return urllib.parse.quote(val,safe="")


def _decode_timetables( html ):
	"""extract session information from timetable html page, returns list of dictionaries"""
	sessionReg = re.compile(r"{[^}]*ourEventId[^}]*}", re.MULTILINE|re.DOTALL)
	commentReg = re.compile(r"\s*//.*", re.MULTILINE)
	dateReg = re.compile(r"new Date\((.*)\)", re.MULTILINE)
	propReg = re.compile(r"(\w*)(:)", re.MULTILINE)

	slots = []

	for match in sessionReg.findall(html):
		match = commentReg.sub("",match)
		match = dateReg.sub(r'"\1"',match)
		match = propReg.sub(r'"\1"\2',match)
		match = match.replace("'", '"')

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

	return slots


def _decode_register( html ):
	"""extract register information from register html page, returns list of tuples"""
	soup = BeautifulSoup( html, "lxml" )

	students = []
	for tr in soup.findAll("tr")[1:]:
		student = tuple([td.text for td in tr.findAll("td")][:4])
		students.append(student)
		
	return students


if __name__ == "__main__":
	currentweek = 11 #cov_week(datetime.datetime.now())

	session = authenticate_session("USERNAME", "PASSWORD")
	slots = get_timetable( session, module="121COM" )

	for s in slots:
		if cov_week(s) != currentweek: continue

		register = get_register( session, s )

		print( "{time} - {room} - {students}".format(room=s["room"], \
													time=s["start"].strftime("%a %H"), \
													students=len(register)) )


	sys.exit(0)

