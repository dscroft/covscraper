import requests
from covscraper import auth
from bs4 import BeautifulSoup
import datetime, sys, re, time
import json
import urllib

class NoStudent(Exception):
    def __init__(self, message):
        self.message = message

def get_student_details( session, uid ):
    url = "https://webapp.coventry.ac.uk/Sonic/Student%20Records/StudentView.aspx?studid={uid}"

    #print(url.format(uid=uid))
    response = session.get(url.format(uid=uid))
      
    return _decode_student( response.text )

def get_attendance( engagement, latest=False ):
    absolute = { "Attended": 0, "On Time": 0, "Absent": 0, "Optional": 0, "Wrong Location": 0, "Late": 0 }
    percent = {"Attended": 0, "On Time": 0}

    if len(engagement["sessions"]) == 0:
      return absolute, percent

    if latest:
      engagement["sessions"] = sorted( engagement["sessions"], key=lambda i: i["start"], reverse=True )

      firstStatus = engagement["sessions"][0]["status"]
      for s in engagement["sessions"]:
        if s["status"] == firstStatus:
          absolute[ firstStatus ] += 1
        else: break

    else:
      for s in engagement["sessions"]:
        if s["status"] in absolute:
          absolute[s["status"]] += 1

    total = sum([ v for k, v in absolute.items() if k != "future"])
    total -= absolute["Optional"]

    absolute["Attended"] = absolute["On Time"] + absolute["Late"]

    percent["Attended"] = absolute["On Time"] + absolute["Late"]
    percent["On Time"]  = absolute["On Time"] 
    #percent["possible"]  = absolute["On Time"] + absolute["Late"] + absolute["future"]

    try:
      percent = { k: v/total*100 for k, v in percent.items() }
    except ZeroDivisionError:
      percent = { k: 0 for k in percent }
        
    return absolute, percent

def get_engagement( session, uid, attempts=5 ):
  url = "https://webapp.coventry.ac.uk/Sonic/Student%20Records/AttendanceMonitoring/IndividualReport.aspx?studentid={uid}" 
   
  for i in range(attempts):
    try:
      response = session.get(url.format(uid=uid))
      return _decode_engagement( response.text )
    except ValueError:
      continue
    #except NoStudent:
    #  raise NoStudent( "No student: " + str(uid) + url.format(uid=uid) )
#     print( response.text )
    #except requests.exceptions.ConnectionError:
    #  continue
    
  return { "sessions": [], "semester": 0.0, "year": 0.0 }

def _decode_engagement( html ):
  soup = BeautifulSoup( html, "lxml" )

  engagementTable = soup.find( "table", {"id":"ctl00_ctl00_BodyContentPlaceHolder_MainContentPlaceHolder_dgvIndividual_ctl00"} )
  if not engagementTable:
    raise NoStudent("Student does not exist")

  # get summary data
  yearAttendance = soup.find("span", {"id":"ctl00_ctl00_BodyContentPlaceHolder_MainContentPlaceHolder_yearAtt"})
  semesterAttendance = soup.find("span", {"id":"ctl00_ctl00_BodyContentPlaceHolder_MainContentPlaceHolder_semesterAtt"})

  result = {"semester": float(semesterAttendance.text.strip("%"))}

  try: result["year"] = float(yearAttendance.text.strip("%"))
  except ValueError: result["year"] = None
 
  # get individual session data
  headers = ("date","start","end","module","room","session","status","type","info")
  sessions = []
  for row in engagementTable.find_all( "tr" ):
    s = {header: val.text for header, val in zip(headers,row.find_all("td"))}
    if s != {}: sessions.append(s)

  for s in sessions:
    s["start"] = datetime.datetime.strptime(s["date"]+" "+s["start"], "%d/%m/%Y %H:%M")
    s["end"] = datetime.datetime.strptime(s["date"]+" "+s["end"], "%d/%m/%Y %H:%M")
    s["date"] = datetime.datetime.strptime(s["date"],"%d/%m/%Y").date()

  #print( [dict(t) for t in {tuple(d.items()) for d in sessions}] )

  sessions = set( tuple(sorted(s.items(),key=lambda i:i[0])) for s in sessions )
  sessions = [ {key: val for key, val in s} for s in sessions ]

  result["sessions"] = sessions

  return result   
  
def _decode_student( html ):
    """extract register information from student information page, returns dict"""
    soup = BeautifulSoup( html, "lxml" )

    if not soup.find("div", {"id":"ctl00_BodyContentPlaceHolder_StudentDetails"}):
        raise NoStudent("Student does not exist")
    
    student = {
        "firstName": soup.find("span", {"id":"ctl00_BodyContentPlaceHolder_txtForename"}),
        "lastName": soup.find("span", {"id":"ctl00_BodyContentPlaceHolder_txtSurname"}),
        "dob": soup.find("span", {"id":"ctl00_BodyContentPlaceHolder_txtDOB"}),
        "gender": soup.find("span", {"id":"ctl00_BodyContentPlaceHolder_txtGender"}),
        "image": soup.find("img", {"id":"ctl00_BodyContentPlaceHolder_imgStudPhoto"}),
        "phone": soup.find("span", {"id":"ctl00_BodyContentPlaceHolder_txtCorrTelNo"}),
        "email": soup.find("a", {"id":"ctl00_BodyContentPlaceHolder_mtEmail"}),
        "modules": [],
        "courses": [],
        "id": soup.find("span", {"id":"ctl00_BodyContentPlaceHolder_txtStudID"})
    }
    
    # === extract text from html tags ===
    for key in ("firstName", "lastName", "dob", "gender", "phone", "email", "id"):
        student[key] = student[key].text
    
    #print( student["image"]["src"] )
    #print( student["image"]["src"][:-10] )

    student["url"] = "https://webapp.coventry.ac.uk/Sonic/Student%20Records/StudentView.aspx?studid="+student["id"]
    student["engageurl"] = "https://webapp.coventry.ac.uk/Sonic/Student%20Records/AttendanceMonitoring/IndividualReport.aspx?studentid="+student["id"]
    student["dob"] = datetime.datetime.strptime(student["dob"], "%d %B %Y").date()
    student["image"] = "https://webapp.coventry.ac.uk/sonic/student%20records/"+student["image"]["src"][:-10]
    
    # === handle the course list ===
    courses = soup.find("table", {"id":"ctl00_BodyContentPlaceHolder_grdProgrammes_ctl00"})
    for row in courses.find("tbody").find_all("tr"):
        course = [ col.text for col in row.find_all("td") ]

        for i in (6,7):
             course[i] = datetime.datetime.strptime(course[i], "%d/%M/%Y").date()
        
        student["courses"].append(course)
    
    # === handle the modules list ===
    modules = soup.find("table", {"id":"ctl00_BodyContentPlaceHolder_grdModules_ctl00"})
    for row in modules.find("tbody").find_all("tr"):
        module = [ col.text for col in row.find_all("td") ]
        
        if len(module) != 8: continue

        if module[5] == "\xa0": module[5] = None
        
        for i in (6,7): 
            module[i] = datetime.datetime.strptime(module[i], "%d/%M/%Y").date()
        
        student["modules"].append(module) 
        
    return student

    
if __name__ == "__main__":
    import getpass

    with open( "temp", "r" ) as f:
      _decode_engagement( f.read() )
    
    sys.exit(0)
