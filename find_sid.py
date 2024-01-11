# converts coventry email or usernames to their student ids

import covscraper
import getpass
import sys

if __name__ == "__main__":
    try:
        username = sys.argv[1]
    except IndexError:
        username = input("Username: ")

    try:
        password = sys.argv[2]
    except IndexError:
        password = getpass.getpass("Password: ")

    session = covscraper.auth.Authenticator(username,password)

    if sys.stdin.isatty():

        try:
            sid = sys.argv[3]
        except IndexError:
            sid = input("Student username/email: ")

        print( covscraper.aulaapi.email_to_id(session, sid.lower().strip() ) )
    else:
        for line in sys.stdin:
            line = line.lower().strip()

            #try:
            sid = covscraper.aulaapi.email_to_id(session, line)
            print( f"{line} {sid}" )
            #except :
            #    print( "ERROR" )