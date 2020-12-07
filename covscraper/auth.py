import requests
from requests_ntlm import HttpNtlmAuth
from bs4 import BeautifulSoup
import datetime, sys, re, os
import json
import urllib
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class AuthenticationFailure(Exception):      
    def __init__(self, message):
        self.message = message

class Authenticator(requests.sessions.Session):
    def __auth_sonic(self, url):
        loginUrl = "https://webapp.coventry.ac.uk/Sonic"

        self.auth = HttpNtlmAuth("COVENTRY\\{}".format(self.username), self.password)
        #response = requests.sessions.Session.get(self, url)
        #self.auth = None

        #return response

    def __auth_kuali(self, url):
        #print(f"__auth_kuali for: {url}")
        #print("Authing Kuali")
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
        #print(f"samlUrl: {samlUrl}\nkey: {key}")
        response = requests.sessions.Session.post(self, samlUrl, data={"SAMLResponse": key})
        #print(f"samlUrl response: {response.text}")
        if response.status_code != 200:
            raise AuthenticationFailure("Failed to post auth code, HTTP {}".format(response.status_code))

        # get the actual page that we were after all this time
        #print(f"Now getting {url}")
        response = requests.sessions.Session.get(self, url)
        #print(f"Actual response: {response.text}")
        #print(response.text)
        #return response
    
    def __auth_engage(self, url):
        loginUrl = "https://engagementdashboard.coventry.ac.uk/login"

        response = requests.sessions.Session.get(self, loginUrl)
        soup = BeautifulSoup( response.text, "lxml" )

        hidden = soup.find("input", {"name": "_csrf"})["value"]
        payload = {"username": self.username,
                 "password": self.password,
                 "_csrf": hidden}
        self.post(loginUrl, data=payload)

        #response = requests.sessions.Session.get(self, url)

        #return response
    
    def __auth_moodle(self, response):
        loginUrl = "https://cumoodle.coventry.ac.uk/login/index.php"

        response = requests.sessions.Session.get(self, loginUrl)
        soup = BeautifulSoup( response.text, "lxml" )
        token = soup.find( "input", {"name": "logintoken"} )["value"]

        data = {"username": self.username, "password": self.password, "logintoken": token}
        response = requests.sessions.Session.post(self, loginUrl, data=data)

        if response.status_code != 200:
          raise AuthenticationFailure("Failed to load Moodle, HTTP {}".format(response.status_code))
          
        #response = requests.sessions.Session.get(self, url)
        #return response
        
	
    domainRegex = re.compile(r"https{,1}://([\w\.\-]{1,})")
    authHandler = {"webapp.coventry.ac.uk": __auth_sonic, \
                   "engagementdashboard.coventry.ac.uk": __auth_engage, \
                   "coventry.kuali.co": __auth_kuali, \
                   "cumoodle.coventry.ac.uk": __auth_moodle }
    redirectPages = ["https://engagementdashboard.coventry.ac.uk/login", \
                     "https://cumoodle.coventry.ac.uk/login/index.php"]

    def __init__(self, username, password):
        requests.sessions.Session.__init__(self)

        self.username = username
        self.password = password

    def __run_handler(self, response):
      domain = self.domainRegex.search(response.url)
      #print(f"Got domain: {domain}")
      if domain:
        domain = domain.group(1)
        try:
          func = self.authHandler[domain]
          func(self,response.url)
        except KeyError: pass
          
        
    def get(self, url, *args, **kwargs):
        #print( url )
        #certfile = os.path.join('/etc/ssl/certs/','ca-bundle.crt')

        response = requests.sessions.Session.get(self, url, verify=False, *args, **kwargs)

        failCondition = lambda response: response.status_code in (401,403,500) or response.url in self.redirectPages
        print(f"response text: {response.text}\ncode: {response.status_code}")
        if failCondition(response):               # if the page failed or we got redirected to anything in redirectPages  
            self.__run_handler( response )
            response = requests.sessions.Session.get(self, url, *args, **kwargs)

        if failCondition(response):               # if it still didn't work give up
            raise AuthenticationFailure("Could not authenticate")
        #print("auth.get: ",end="")
        #print(response.text)
        return response

    def post(self,url, *args, **kwargs):
        response = requests.sessions.Session.post(self, url, *args, **kwargs)

        failCondition = lambda response: response.status_code in (401,403) or response.url in self.redirectPages
             
        if failCondition(response):               # if the page failed or we got redirected to anything in redirectPages
            self.__run_handler( response )
            response = requests.sessions.Session.post(self, url, *args, **kwargs)
                
        if failCondition(response):               # if it still didn't work give up
            raise AuthenticationFailure("Could not authenticate")

        return response
		


def url_safe( val ):
    return urllib.parse.quote(val,safe="")

if __name__ == "__main__":
    auth = Authenticator(sys.argv[1], sys.argv[2])

    response = auth.get("https://cumoodle.coventry.ac.uk/grade/report/grader/index.php?id=47437")
    print(response.text)
    print()
    
    #response = auth.get("https://webapp.coventry.ac.uk/Timetable-main")
    #print(response)

    #response = auth.get("https://engagementdashboard.coventry.ac.uk/attendance/all?id=7203071")
    #print(response)
	
