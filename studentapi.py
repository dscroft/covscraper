import requests
from auth import *
from bs4 import BeautifulSoup
import datetime, sys, re
import json
import urllib

class NoStudent(Exception):
	def __init__(self, message):
		self.message = message

def get_student_details( session, uid):
	url = "https://webapp.coventry.ac.uk/Sonic/Student%20Records/StudentView.aspx?studid={uid}"

	print(url.format(uid=uid))
	response = session.get(url.format(uid=uid))
  
	return _decode_student( response.text )


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
		"modules": []
	}
	
	# === extract text from html tags ===
	for key in ("firstName", "lastName", "dob", "gender", "phone", "email"):
		student[key] = student[key].text
	
	student["dob"] = datetime.datetime.strptime(student["dob"], "%d %B %Y").date()
	student["image"] = "https://webapp.coventry.ac.uk/sonic/student%20records/"+student["image"]["src"][3:-10]
	
	# === handle the modules list ===
	modules = soup.find("table", {"id":"ctl00_BodyContentPlaceHolder_grdModules_ctl00"})
	for row in modules.find("tbody").find_all("tr"):
		module = [ col.text for col in row.find_all("td") ]
		
		if module[5] == "\xa0": module[5] = None
		
		for i in (6,7): 
			module[i] = datetime.datetime.strptime(module[i], "%d/%M/%Y").date()
		
		student["modules"].append(module) 
		
	return student

	
if __name__ == "__main__":
	import getpass

	session = authenticate_session(input("username:"), getpass.getpass("password:"))
	student = get_student_details( session, uid=input("student uid:") )
	
	
	print(student)
	
	sys.exit(0)
