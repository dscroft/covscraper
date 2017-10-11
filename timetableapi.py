import requests
from auth import *
from bs4 import BeautifulSoup
import datetime, sys, re
import json
import urllib

WEEKOFFSET = { "2016-2017": datetime.date(2016,7,17), \
			   "2017-2018": datetime.date(2017,7,16) }

def get_lecturer_timetable( session, date=datetime.datetime.now() ):
	"""get the sessions timetabled for the person used to authenticate the current session"""
	url = "https://webapp.coventry.ac.uk/Timetable-main/Timetable/Lecturer#year={year}&month={month}&day={day}&view=agendaWeek"

	response = session.get(url.format(year=date.year, month=date.month, day=date.day))

	return _decode_timetables( response.text )


def get_timetable( session, module="", room="", course="", uid="", date=datetime.datetime.now() ):
	"""get the sessions timetabled for a given module, room, student uid, course or any combination thereof"""
	url = "https://webapp.coventry.ac.uk/Timetable-main/Timetable/Search?CourseId={course}&ModuleId={module}&RoomId={room}&queryStudent={uid}&studentId={uid}&viewtype=%2F&searchsetid={academicyear}&queryModule={module}&queryRoom={room}&queryCourse={course}&timetabletype=normal"

	academicyear = academic_year(date)

	url = url.format(module=url_safe(module), room=url_safe(room), course=url_safe(course), uid=uid, academicyear=academicyear)
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

	
	response = session.get(url)

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


def _decode_timetables( html ):
	"""extract session information from timetable html page, returns list of dictionaries"""
	sessionReg = re.compile(r"{[^}]*ourEventId[^}]*}", re.MULTILINE|re.DOTALL)
	commentReg = re.compile(r"\s*//.*", re.MULTILINE)
	quoteReg = re.compile( r"(^\"[^\"]*\":\s*\".*)(\")(.*\"[,\r\n])", re.MULTILINE ) 
	dateReg = re.compile(r"new Date\((.*)\)", re.MULTILINE)
	propReg = re.compile(r"(\w*)(:)", re.MULTILINE)
	
	slots = []

	for match in sessionReg.findall(html):
		match = commentReg.sub("",match)
		match = dateReg.sub(r'"\1"',match)
		match = propReg.sub(r'"\1"\2',match)
		match = match.replace("'", '"')
		
		# what complete bastard puts unescaped quotes in a string?
		while quoteReg.search(match):
			match = quoteReg.sub(r"\1\3", match)
		
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
	for tr in soup.findAll("tr")[1:]:
		student = [td.text for td in tr.findAll("td")][:4]
		student[1] = int(student[1])
		if student[3] == "": student[3] = None
		students.append(tuple(student))
		
	return students


if __name__ == "__main__":
	import getpass, getopt
	from rooms import ROOMS
	
	usageTxt = "help"
	
	params = {"user": None, "pass": None, "room": "", "module": "", "course": "", "uid": "", "date": None}
	week = cov_week(datetime.datetime.now())
	
	# configure flags
	shortopts = "".join(["{:.1}:".format(i) for i in params])
	longopts = ["help"]+["{}=".format(i) for i in params]
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
		
	if not params["user"]: params["user"] = input("username: ")
	if not params["pass"]: params["pass"] = getpass.getpass("password: ")
		
	currentweek = cov_week(params["date"])

	# authenticate and get the timetable
	session = authenticate_session(params["user"], params["pass"])
	slots = get_timetable( session, module=params["module"], room=params["room"], course=params["course"], uid=params["uid"], date=params["date"] )
	
	# pretty printing
	print( "Time   - Room     - Enr -> Stu/Cap - Module" )
	for s in slots:
		if cov_week(s) != currentweek: continue

		register = get_register( session, s )

		try:
			capacity = int(ROOMS[s["room"]]["size"])
		except (KeyError, TypeError):
			capacity = "?"
			
		module = s["title"].split(", ")
		module = module[0]+"..." if len(module) > 1 else module[0]	
	
		print( "{time} - {room:8} - {enrolled:3} -> {students:3}/{capacity:<3} - {module}".format(room=s["room"], \
													time=s["start"].strftime("%a %H"), \
													students=len(register), \
													enrolled=len([i for i in register if i[3]]), \
			 										capacity=capacity, \
													module=module) )


	sys.exit(0)
