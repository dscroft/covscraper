import requests, sys
import json
import datetime, csv, io

class Codio:
	def __init__(self, username, password):
		self.__session, self.__sessionId = Codio.__login( username, password )

	def __login(username, password):
		session = requests.Session()
		session.headers.update({"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36"})

		# login
		url = "https://codio.co.uk/service/"
		data = {"object":"AccountManager","method":"login","data":{"user_name":username,"password":password,"type":"password","isRememberMe":False}}
		headers = {"Content-Type":"application/json"}

		response = session.post( url, data=json.dumps(data), headers=headers )

		sessionId = json.loads(response.text)["response"]["session_id"]

		return session, sessionId

	def __decode_engagement_data(jdata):
		engagement = {}
		for student, data in jdata["response"].items():
			engagement[student] = {"time":data["timeSpent"],
								   "answered":data["assessmentScore"],
								   "proportion":data["assessmentScore"]/data["maxAssessmentScore"] if data["maxAssessmentScore"] else 1.0}
		return engagement

	def __decode_class_data( jdata ):
		students = {}
		teachers = {}
		units = {}
		classes = {}
		for data in jdata["response"]:
			_students = { s["id"]:{"username":s["name"], "name":s["actualName"]} for s in data["studentsFull"] }
			_teachers = { s["id"]:{"username":s["name"], "name":s["actualName"]} for s in data["teachersFull"] }
			_units = {}
			for _, module in data["modules"].items():
				_units.update({ u["id"]:{"name":u["name"]} for u in module["units"] })

			students.update(_students)
			teachers.update(_teachers)
			units.update(_units)

			classes[data["id"]] = {"name":data["name"],
									"units":set(_units.keys()),
									"students":set(_students.keys()),
									"teachers":set(_teachers.keys()) }

		for key, val in classes.items():
			for unit in val["units"]:
				units[unit]["class"] = key;

		return classes, units, students, teachers

	def __decode_organisation_data( jdata ):
		organisations = {}
		for data in jdata["response"]:
			organisations[data["id"]] = {"name":data["details"]["name"],
										"members":data["membersCount"]}
		return organisations

	def __decode_ip_consent_data( text ):
		consent = {}
		date_fmt = "%a %b %d %H:%M:%S %Z %Y"
		reader = csv.DictReader( io.StringIO(text) )
		for row in reader:
			if not row["Date"]: continue

			username = row["Codio Name"]
			date = datetime.datetime.strptime( row["Date"], date_fmt )
			email = row["Email"]
						
			if username not in consent:
				consent[username] = {"versions":set(),
									 "email": email,
									 "latest":date,
									 "signup":date}

			if date < consent[username]["signup"]: consent[username]["signup"] = date
			if date > consent[username]["latest"]: 
				consent[username]["latest"] = date
				consent[username]["email"] = email

			consent[username]["versions"].add(int(row["Revision"]))				

		return consent

	def __decode_account_details( jdata ):
		data = jdata["response"]

		return {"email":data["details"]["email"],
				"username":data["details"]["name"],
				"name":data["details"]["actual_name"],
				"teacher":data["details"]["type"]=="TEACHER"}

	def __decode_students( jdata ):
		students = {}
		for data in jdata["response"]:
			students[data["id"]] = {"name":data["actualName"],"username":data["name"]}
		return students

	def get_students(self, orgCode):
		url = "https://apollo.codio.co.uk/api"
		data = {"object":"class",
				"method":"getAggregatedEduTeamMembers",
				"data":{"organizationId":orgCode,
						"teamSlug":"students"},
				"params":{"session_id":self.__sessionId}}
		headers = {"Content-Type":"application/json"}

		response = self.__session.post( url, data=json.dumps(data), headers=headers )
		return Codio.__decode_students( json.loads(response.text) )

	def get_account_details(self,uid):
		url = "https://codio.co.uk/service"
		data = {"object":"AccountManager","method":"getAccount","data":{"id":uid}}
		headers = {"Content-Type":"application/json"}

		response = self.__session.post( url, data=json.dumps(data), headers=headers )
		return Codio.__decode_account_details( json.loads(response.text) )

	def get_organisation_details(self):
		# get organisation info
		url = "https://codio.co.uk/service/"
		data = {"object":"OrganizationManager","method":"getMyOrganizations"}
		headers = {"Content-Type":"application/json"}

		response = self.__session.post( url, data=json.dumps(data), headers=headers )
		return Codio.__decode_organisation_data( json.loads(response.text) )

	def get_ip_consent(self, orgCode):				
		# get IP consent data
		url = "https://codio.co.uk/service/raw?ip-consent=1&orgId={}".format(orgCode)
		response = self.__session.get( url )
		return Codio.__decode_ip_consent_data( response.text )

	def get_class_details(self, emails=True):
		# get class info
		url = "https://apollo.codio.co.uk/api"
		data = {"object":"class","method":"find","data":{},"params":{"session_id":self.__sessionId}}
		headers = {"Content-Type":"application/json"}

		response = self.__session.post( url, data=json.dumps(data), headers=headers )
		classes, units, students, teachers = Codio.__decode_class_data( json.loads(response.text) )

		if emails:
			users = {}
			for orgCode in self.get_organisation_details().keys():
				users.update(self.get_ip_consent(orgCode))
			for k,v in students.items():
				try: students[k]["email"] = users[v["username"]]["email"]
				except KeyError: pass

		return classes, units, students, teachers

	def get_engagement_details(self, classCode, unitCode):
		# get engagement data
		url = "https://apollo.codio.co.uk/api"
		data = {"object":"class","method":"getStudentStats","data":{"id":classCode,"unitId":unitCode},"params":{"session_id":self.__sessionId}}
		headers = {"Content-Type":"application/json"}

		response = self.__session.post( url, data=json.dumps(data), headers=headers )
		return Codio.__decode_engagement_data( json.loads(response.text) )

	
	def _remove_student(self, studentId, orgId, forReal=False):
		if not forReal: return False

		# removes dummy students
		#url = "https://codio.co.uk/service/"
		#data = {"object":"OrganizationManager","method":"removeDummyAccount","data":{"orgId":orgId, "dummyId":studentId}}
		#headers = {"Content-Type":"application/json"}
		#response = self.__session.post( url, data=json.dumps(data), headers=headers )

		url = "https://codio.co.uk/service"
		data = {"object":"OrganizationManager","method":"removeMembers","data":{"orgId":orgId,"memberIds":[studentId]}}
		headers = {"Content-Type":"application/json"}

		response = self.__session.post( url, data=json.dumps(data), headers=headers )
		studentIds = [ i["id"] for i in json.loads( response.text )["response"] ]
		print(studentIds)
		return studentId not in studentIds

if __name__ == "__main__":
	import re

	codio = Codio("ac0745@coventry.ac.uk","")
	

	organisation = codio.get_organisation_details()
	print( organisation )

	classes, units, students, teachers = codio.get_class_details()
	for key, val in students.items():
		if "aaa" in val["name"]:
			print( key, val )

	orgId = "4aa0a172-ce09-41c8-a361-872bca239cfc"
	removeId = "f6875630-6636-4627-838f-65529f586eff"

	#print( ">", codio._remove_student( removeId, orgId, True ) )


#{"object":"OrganizationManager","method":"removeDummyAccount","data":{"orgId":"4aa0a172-ce09-41c8-a361-872bca239cfc","dummyId":"00112233-4455-6677-abe0-6d9465be9bdb"}}


# remove from students
#{"object":"class","method":"removeFromAggregatedEduTeam","data":{"organizationId":"4aa0a172-ce09-41c8-a361-872bca239cfc","teamSlug":"students","memberIds":["f6875630-6636-4627-838f-65529f586eff"]},"params":{"session_id":"0e39c2c8-66b6-456f-8fc6-7de2841aa6c8"}}


# remove from org
#{"object":"OrganizationManager","method":"removeMembers","data":{"orgId":"4aa0a172-ce09-41c8-a361-872bca239cfc","memberIds":["f6875630-6636-4627-838f-65529f586eff"]}}

	
