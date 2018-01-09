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

    def __auth_kuali(self, url):
        kualiUrl = "https://coventry.kuali.co/auth?return_to=https%3A%2F%2Fcoventry.kuali.co%2Fapps%2F"
        shibbolethUrl = "https://idp2.coventry.ac.uk/idp/Authn/UserPassword"
        
        # shibboleth wont let us connect unless it looks like we've been redirected from an approved site
        response = requests.sessions.Session.get(self, kualiUrl)
        if response.status_code != 200:
          raise AuthenticationFailure("Failed to load Kuali, HTTP {}".format(response.status_code))

        # post the auth data to shibboleth
        data = {"j_username": self.username, "j_password": self.password}
        response = requests.sessions.Session.post(self, shibbolethUrl, data=data)
        if response.status_code != 200:
          raise AuthenticationFailure("Failed to load shibboleth, HTTP {}".format(response.status_code))

        # extract the auth key and post it
        soup = BeautifulSoup( response.text, "lxml" )
        samlUrl = soup.find( "form", {"method": "post"} )["action"]
        key = soup.find( "input", {"name": "SAMLResponse"} )["value"]
        response = requests.sessions.Session.post(self, samlUrl, data={"SAMLResponse": key})
        if response.status_code != 200:
          raise AuthenticationFailure("Failed to post auth code, HTTP {}".format(response.status_code))
        
        # get the actual page that we were after all this time
        response = requests.sessions.Session.get(self, url)
        
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
                   "engagementdashboard.coventry.ac.uk": __auth_engage, \
                   "coventry.kuali.co": __auth_kuali}
    redirectPages = ["https://engagementdashboard.coventry.ac.uk/login"]

    def __init__(self, username, password):
        requests.sessions.Session.__init__(self)

        self.username = username
        self.password = password
		
    def get(self, url, stream=False):
        response = requests.sessions.Session.get(self, url, stream=stream)

        failCondition = lambda response: not response or response.status_code in (401,403) or response.url in self.redirectPages
             
        if failCondition(response):               # if the page failed or we got redirected to anything in redirectPages
            domain = self.domainRegex.search(response.url) # figure out what domain we ended up at

            if domain:
                domain = domain.group(1)
                try:
                  func = self.authHandler[domain] # see if we know how to authenticate on this domain
                  response = func(self, url)      # authenticate
                except KeyError: pass

        if failCondition(response):               # if it still didn't work give up
            raise AuthenticationFailure("Could not authenticate")

        return response

		
		


def url_safe( val ):
    return urllib.parse.quote(val,safe="")

if __name__ == "__main__":
    auth = Authenticator(sys.argv[1], sys.argv[2])

    response = auth.get("https://coventry.kuali.co/api/v0/cm/search/results.csv?status=active&index=courses_latest&q=122COM")
    print(response.text)
    print()
    
    #response = auth.get("https://webapp.coventry.ac.uk/Timetable-main")
    #print(response)

    #response = auth.get("https://engagementdashboard.coventry.ac.uk/attendance/all?id=7203071")
    #print(response)
	