# Script to check the clearing website for new callbacks and notify me if there are any
# Uses notify.run to send the notifications

import covscraper
import pickle
import sys
import codioscraper, re
import bs4
import time
import pickle

seen = pickle.lo

def check():
    seen = pickle.load( open( "seen.pickle", "rb" ) )

    session = covscraper.auth.Authenticator(sys.argv[1], sys.argv[2])

    response = session.get( "https://webapp.coventry.ac.uk/ASonic/Clearing/WaitingListReport" )

    data = {"Faculty": "",
            "School": "",
            "ReportType": "PCALLBACK",
            "DateFrom": "13/08/2020" }

    response = session.post( "https://webapp.coventry.ac.uk/ASonic/Clearing/WaitingListReport", data )

    soup = bs4.BeautifulSoup( response.text, "lxml" )

    before = len(seen)
    for row in soup.find("table").find_all("tr")[1:]:
        cols = row.find_all("td")
        uid, school = cols[0].text, cols[3].text

        if school == "EXR":
            seen.add( uid )

    after = len(seen)

    if after > before:
        print( "Callback ", seen )
        os.system( f'curl https://notify.run/WvuSasgiItrOxxFq -d "New callbacks"' )

    pickle.dump( seen, open("seen.pickle","wb") )

if __name__ == "__main__":


    while True:
        try:
            print( "Running" )
            check()
        except:
            print( "Error:", sys.exc_info()[0] )

        time.sleep(60)
