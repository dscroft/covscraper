# convert a list of student ids into an html page with their pictures
# useful for recognising students in a class

import covscraper
import getpass
import sys
import base64
import re

def process( session, username ):
    if username.isdigit():
        sid = username
    else:
        sid = covscraper.aulaapi.email_to_id(session, username)
    details = covscraper.studentapi.get_student_details( session, sid )

    return details

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

    sys.stdout.write( "<html>\n<body>\n" )

    if sys.stdin.isatty():

        try:
            sid = sys.argv[3]
        except IndexError:
            sid = input("Student username/email: ")

        print( process(session, sid) )
    else:
        for line in sys.stdin:
            line = line.strip()

            try:
                details = process( session, line )

                response = session.get( details["image"] )

                image = f"data:{response.headers['Content-Type']};base64,{str(base64.b64encode(response.content).decode('utf-8'))}"

                sys.stdout.write( f"<b>{details['firstName']} {details['lastName']}</b></br>\n")
                sys.stdout.write( f'<img src="{image}" /><br><br>\n' )
            except covscraper.studentapi.NoStudent:
                pass

    sys.stdout.write( "</body>\n</html>\n" )