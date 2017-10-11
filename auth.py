import requests
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
import datetime, sys, re
import json
import urllib

class AuthenticationFailure(Exception):
	def __init__(self, message):
		self.message = message

def authenticate_session( user, password ):
	"""log into the timetable system"""
	url = "https://webapp.coventry.ac.uk/Timetable-main"
	#headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}

	session = requests.Session()
	session.auth = HttpNtlmAuth("COVENTRY\\{}".format(user), password)
	response = session.get(url)

	if response.status_code == 401:
		raise AuthenticationFailure("Failed to connect to timetable system")
	
	return session

def url_safe( val ):
	return urllib.parse.quote(val,safe="")