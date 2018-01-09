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
        loginUrl = "https://coventry.kuali.co/auth?return_to=https%3A%2F%2Fcoventry.kuali.co%2Fapps%2F"

        response = requests.sessions.Session.get(self, loginUrl)
        
        postUrl = "https://idp2.coventry.ac.uk/idp/Authn/UserPassword"
        

        response = requests.sessions.Session.post(self, loginUrl, data={"j_username": self.username, "j_password": self.password})
        
        print( response.text )
        
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
                   "engagementdashboahttps://coventry.kuali.co/api/v0/cm/search/results.csv?status=active&index=courses_latest&q=rd.coventry.ac.uk": __auth_engage, \
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
    import io, csv
    module = "122COM"

    session = requests.Session()
    
    response = session.get( "https://coventry.kuali.co/auth?return_to=https%3A%2F%2Fcoventry.kuali.co%2Fapps%2F" )
    if response.status_code != 200:
      print( "error1" )
      
    data = {"j_username": sys.argv[1], "j_password": sys.argv[2]}
    response = session.post( "https://idp2.coventry.ac.uk/idp/Authn/UserPassword", data=data )
    if response.status_code != 200:
      print( "error2" )
      
    soup = BeautifulSoup( response.text, "lxml" )
    
    url = soup.find( "form", {"method": "post"} )["action"]
    key = soup.find( "input", {"name": "SAMLResponse"} )["value"]
    
    response = session.post( url, data={"SAMLResponse": key} )
    
    # have to use a search param as doesn't return all the modules
    url = "https://coventry.kuali.co/api/v0/cm/search/results.csv?index=courses_latest&q={module}".format(module=module)
    response = session.get( url )
     
    # extract csv data
    csvfile = io.StringIO( response.text )
    csvdata = list( csv.reader( csvfile, delimiter=',' ) )
   
    # convert to dict of dicts, key is module code
    modules = {}
    modulesUid = {}
    headers = csvdata[0]
    for row in range(1,len(csvdata)):
      fields = { key: val for key, val in zip(headers, csvdata[row]) }           
      modules[fields["reversedCode"]] = fields
      modulesUid[fields["reversedCode"]] = fields["id"]
      
    # get actual damn MID
    url = "https://coventry.kuali.co/api/cm/courses/changes/{uid}?denormalize=true".format(uid=modulesUid[module])
    response = session.get(url)
    
    middata = json.loads( response.text )
    
    print( middata )
        
   
    
    
  
    #auth = Authenticator(sys.argv[1], sys.argv[2])

    #response = auth.get("https://coventry.kuali.co/api/v0/cm/search/results.csv?status=active&index=courses_latest&q=")
    #print(response)
    #print()
    
    #response = auth.get("https://webapp.coventry.ac.uk/Timetable-main")
    #print(response)

    #response = auth.get("https://engagementdashboard.coventry.ac.uk/attendance/all?id=7203071")
    #print(response)
	