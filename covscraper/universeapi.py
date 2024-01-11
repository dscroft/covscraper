import requests
#from covscraper import auth
import auth
from bs4 import BeautifulSoup
import datetime, sys, re
import json
import urllib

class NoStudent(Exception):
    def __init__(self, message):
        self.message = message

def get_marks( session, module, date ):
    url = "https://webapp.coventry.ac.uk/Sonic/Exams/MarksEntry.aspx?modid={module}&effdate={date}&sgridpage={page}"

    #print(url.format(uid=uid))
    page = 0
    response = session.get(url.format(module=module,date=date,page=page))
    print( response.text )
    #return _decode_student( response.text )


def _decode_marks( html ):
    """extract register information from student information page, returns dict"""
    soup = BeautifulSoup( html, "lxml" )



    headers = [ header.text for header in soup.find_all( "th", {"class":"rgHeader"} ) ]

    students = []
    for row in soup.find_all( "tr", {"class":"rgEditRow"} ):
        students.append( [ cell.text for cell in row.find_all( "td" ) ] )

    

    pages = soup.find( "div", {"class":"rgInfoPart"} )
    pages = int(re.search( r"[0-9]{1,} items in ([0-9]{1,}) pages", pages.text ).group(1))
    
    return headers, students, pages

    
if __name__ == "__main__":
    import getpass

    with open( "test.html", "r" ) as f:
        html = f.read()

    _decode_marks( html )

    sys.exit()


    session = auth.Authenticator("ac0745", "password")
    marks = get_marks( session, "122COM", "1/3/2018" )
    
    
    print("done")
    
    sys.exit(0)
