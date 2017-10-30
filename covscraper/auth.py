import requests
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
import datetime, sys, re
import json
import urllib

class AuthenticationFailure(Exception):
	def __init__(self, message):
		self.message = message

class Authenticator(requests.sessions.Session):
	def __auth_sonic(self, url):
		loginUrl = "https://webapp.coventry.ac.uk/Sonic"
		
		self.auth = HttpNtlmAuth("COVENTRY\\{}".format(self.username), self.password)
		response = requests.sessions.Session.get(self, url)
		self.auth = None
		
		return response

	def __auth_engage(self, url):
		loginUrl = "https://engagementdashboard.coventry.ac.uk/login"
		
		response = requests.sessions.Session.get(self, loginUrl)
		soup = BeautifulSoup( response.text, "lxml" )
		
		hidden = soup.find("input", {"name": "_csrf"})["value"]
		payload = {"username": self.username,
			       "password": self.password,
			       "_csrf": hidden}
		self.post(loginUrl, data=payload)
		
		response = requests.sessions.Session.get(self, url)
		
		return response
	
	domainRegex = re.compile(r"https{,1}://([\w\.\-]{1,})")
	authHandler = {"webapp.coventry.ac.uk": __auth_sonic, \
				   "engagementdashboard.coventry.ac.uk": __auth_engage}
	redirectPages = ["https://engagementdashboard.coventry.ac.uk/login"]
	
	def __init__(self, username, password):
		requests.sessions.Session.__init__(self)
		
		self.username = username
		self.password = password
		
	def get(self, url):
		response = requests.sessions.Session.get(self, url)
		
		failCondition = lambda response: response.status_code in (401,403) or response.url in self.redirectPages
		
		if failCondition(response):
			domain = self.domainRegex.search(response.url)
			if domain:
				domain = domain.group(1)
				try:
					func = self.authHandler[domain]
					response = func(self, url)					
				except KeyError: pass
		
		if failCondition(response):
			raise AuthenticationFailure("Could not authenticate")
					
		return response
				
		
		


def url_safe( val ):
	return urllib.parse.quote(val,safe="")

if __name__ == "__main__":
	auth = Authenticator("", "")
	
	response = auth.get("https://webapp.coventry.ac.uk/Timetable-main")
	print(response)
	
	response = auth.get("https://engagementdashboard.coventry.ac.uk/attendance/all?id=7203071")
	print(response)
	