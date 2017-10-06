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
	url = "https://webapp.coventry.ac.uk/sonic/student%20records/Monitoring/studentmonitoring.aspx?studentid={uid}"

	response = session.get(url.format(uid=uid))
  
	return _decode_student( response.text )


def _decode_student( html ):
	"""extract register information from student information page, returns dict"""
	soup = BeautifulSoup( html, "lxml" )

	if not soup.find("div", {"id": "ctl00_ctl00_BodyContentPlaceHolder_MainContentPlaceHolder_StudentDetails_StudentDetailsPanel"}):
		raise NoStudent("Student does not exist")
	
	student = {
		"firstName": soup.find("span", {"id": "ctl00_ctl00_BodyContentPlaceHolder_MainContentPlaceHolder_StudentDetails_StudentFirstName"}),
		"lastName": soup.find("span", {"id":"ctl00_ctl00_BodyContentPlaceHolder_MainContentPlaceHolder_StudentDetails_StudentLastName"}),
		"dob": soup.find("span", {"id":"ctl00_ctl00_BodyContentPlaceHolder_MainContentPlaceHolder_StudentDetails_DateOfBirth"}),
		"gender": soup.find("span", {"id":"ctl00_ctl00_BodyContentPlaceHolder_MainContentPlaceHolder_StudentDetails_StudentGender"}),
		"image": soup.find("img", {"id":"ctl00_ctl00_BodyContentPlaceHolder_MainContentPlaceHolder_StudentDetails_StudentImage"})
	}
	   
	for key in ("firstName", "lastName", "dob", "gender"):
		student[key] = student[key].text
	
	student["dob"] = datetime.datetime.strptime(student["dob"], "%d %B %Y").date()
	student["image"] = "https://webapp.coventry.ac.uk/sonic/student%20records/"+student["image"]["src"][3:-10]
   
	return student

	
if __name__ == "__main__":
	import getpass

	session = authenticate_session(input("username:"), getpass.getpass("password:"))
	student = get_student_details( session, uid=input("student uid:") )
	
	print(student)
	
	sys.exit(0)
