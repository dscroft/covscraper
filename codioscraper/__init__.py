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


    #sessionId = json.loads(response.text)["response"]["session_id"]
    sessionId = None

    print( response.text )

    return session, sessionId

  def __decode_engagement_data(jdata):
    engagement = {}
    for student, data in jdata.get("response",{}).items():
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

    try:
      return {"email":data["details"]["email"],
         "username":data["details"]["name"],
         "name":data["details"]["actual_name"],
         "teacher":data["details"]["type"]=="TEACHER"}
    except:
      raise ValueError( jdata["response"]["message"] )

  def __decode_students( jdata ):
    students = {}
    for data in jdata["response"]:
      students[data["id"]] = {"name":data["actualName"],"username":data["name"]}
    return students

  def get_class_token(self, classCode):
    url = "https://apollo.codio.co.uk/api"
    data = {"object":"class",
        "method":"findOne",
        "data":{"id":classCode},
        "params":{"session_id":self.__sessionId}}
    headers = {"Content-Type":"application/json"}
    
    response = self.__session.post( url, data=json.dumps(data), headers=headers )
    return json.loads(response.text)["response"]["invitation_token"]

  #def get_students(self, orgCode):
  #  url = "https://apollo.codio.co.uk/api"
  #  data = {"object":"class",
  #      "method":"getAggregatedEduTeamMembers",
  #      "data":{"organizationId":orgCode,
  #          "teamSlug":"students"},
  ##      "params":{"session_id":self.__sessionId}}
  #  headers = {"Content-Type":"application/json"}
#
#    response = self.__session.post( url, data=json.dumps(data), headers=headers )
#    print( response.text )
#    return Codio.__decode_students( json.loads(response.text) )

  def get_students( self, orgCode ):
    url = "https://codio.co.uk/service"
    data = {"object":"OrganizationManager","method":"removeMembers","data":{"orgId":orgCode,"memberIds":[12345]}}
    headers = {"Content-Type":"application/json"}

    response = self.__session.post( url, data=json.dumps(data), headers=headers )

    data = [ ( i["name"], i["id"] ) for i in json.loads( response.text )["response"] ]

    return data

  def get_accounts(self, orgCode):
    url = "https://codio.co.uk/service/"
    data = {"object":"OrganizationManager",
        "method":"getMembers",
        "data":{"orgId":orgCode,
            "teamName":"all-members"},
        "params":{"session_id":self.__sessionId}}
    headers = {"Content-Type":"application/json"}
        
    response = self.__session.post( url, data=json.dumps(data), headers=headers )
    return Codio.__decode_students( json.loads(response.text) )   
  
  def get_account_details(self,username):
    url = "https://codio.co.uk/service"
    #data = {"object":"AccountManager","method":"getAccount","data":{"id":uid}}
    data = {"object":"AccountManager","method":"getAccount","data":{"name":username}}
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

  def get_class_details(self, emails=True, tokens=True):
    # get class info
    url = "https://apollo.codio.co.uk/api"
    data = {"object":"class","method":"find","data":{},"params":{"session_id":self.__sessionId}}
    headers = {"Content-Type":"application/json"}

    response = self.__session.post( url, data=json.dumps(data), headers=headers )
    classes, units, students, teachers = Codio.__decode_class_data( json.loads(response.text) )

    if tokens:
      for c in classes:
        classes[c]["token"] = self.get_class_token( c )

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

  def get_projects(self, username):
  	url = "https://codio.co.uk/service/"
  	data = {"object":"ProjectManager","method":"getPublicProjects","data":{"name":username}}
  	headers = {"Content-Type":"application/json"}

  	response = self.__session.post( url, data=json.dumps(data), headers=headers )
  	return json.loads(response.text)["response"]["public"]


  	#for key, data in json.loads(response.text).items():
  	#	print( key, data )
  
  def _remove_student(self, studentId, orgId, forReal=False):
    if not forReal: return False

    # removes dummy students
    #url = "https://codio.co.uk/service/"
    #data = {"object":"OrganizationManager","method":"removeDummyAccount","data":{"orgId":orgId, "dummyId":studentId}}
    #headers = {"Content-Type":"application/json"}
    #response = self.__session.post( url, data=json.dumps(data), headers=headers )

    url = "https://codio.co.uk/service"
    data = {"object":"OrganizationManager","method":"removeMembers","data":{"orgId":orgId,"memberIds":[studentId]}}
    #data = {"object":"OrganizationManager", "method":"listMembers","data":{"orgId":orgId}}
    headers = {"Content-Type":"application/json"}

    response = self.__session.post( url, data=json.dumps(data), headers=headers )
    studentIds = [ i["id"] for i in json.loads( response.text )["response"] ]
    #print(studentIds)
    return studentId not in studentIds

if __name__ == "__main__":
  import re

  codio = Codio(sys.argv[1], sys.argv[2])

  organisation = list(codio.get_organisation_details().keys())[0]
  print( organisation )

  accounts = codio.get_accounts( organisation )

  for key in accounts:
    details = codio.get_account_details(key)
    if details["teacher"]:
      print( details["email"] )

  sys.exit()

  

  today = datetime.datetime.now()

  classCode = "5d6d1810a5d5d4418793b91e"

  print( codio.get_class_details()[0] )


  sys.exit()


  accounts = codio.get_accounts( organisation )
  print(len(accounts))
  sys.exit()
  for count, _ in enumerate(accounts.items()):
  	key, data = _
  	#if count > 3: break

  	projects = codio.get_projects( data["username"] )

  	try:
  		latest = max([ datetime.datetime.utcfromtimestamp(int(i["accessTime"])/1000) for i in projects ])
  		diff = (today - latest).total_seconds() // 3600
  	except ValueError:
  		latest = None
  		diff = None

  	if latest == None or (today - latest) > datetime.timedelta(days=28):
  	 	print( "{}|{}|{}".format(data["username"],latest,diff))
  	
  


  sys.exit()


  codio = Codio(sys.argv[1], sys.argv[2])
  

  organisation = list(codio.get_organisation_details().keys())[0]
  print( organisation )

  accounts = codio.get_accounts( organisation )

  for count, account in enumerate(accounts):
  	if count > 2: break
  	
  	print( count, accounts[account] )

  	print( codio.get_projects( accounts[account]["username"] ) )

  	print()



  #classes, units, students, teachers = codio.get_class_details()
  #for key, val in students.items():
  #  if "aaa" in val["name"]:
  #    print( key, val )




#