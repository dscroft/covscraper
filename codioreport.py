# Generate a csv containing the list of students in codio and their course details

import getpass, getopt
import codioscraper
import datetime
import sys, json
import re
from itertools import islice
import logging
import covscraper


def main( user, cpass, upass, output ):
    logger = logging.getLogger(__name__)

    logger.info( "Connect to Aula" )
    session = covscraper.auth.Authenticator( user, upass )

    with open( output, "w" ) as f:
        f.write( "codio_email,codio_username,codio_teacher,sid,forename,surname,course_code,course,qualification,stage,start,end,info\n" )

        for user in get_codio_users( user, cpass ):
            print( user["email"] )

            sid = covscraper.aulaapi.email_to_id( session, user["email"] )

            forename, surname, infourl = get_student_details( session, sid )
            code, title, qual, mode, stage, location, start, end = get_course_details( session, sid )

            f.write( f"{user['email']},{user['username']},{user['teacher']},{sid if sid else ''},{forename},{surname},{code},{title},{qual},{stage},{start},{end},{infourl}\n" )

def get_student_details( session, sid ):
    try:
        details = covscraper.studentapi.get_student_details( session, sid )
        return details["firstName"], details["lastName"], details["url"]
    except covscraper.studentapi.NoStudent:
        return [""]*3

def get_course_details( session, sid ):
    try:
        details = covscraper.studentapi.get_student_details( session, sid )
        return sorted( details["courses"], key=lambda i: i[7] )[-1]
    except covscraper.studentapi.NoStudent:
        return [""]*8


def get_codio_users( user: str, cpass: str ):
    logger = logging.getLogger(__name__)
    
    logger.info( "Connect to codio" )
    codio = codioscraper.Codio( f"{user}@coventry.ac.uk", cpass )

    logger.info( "Get organisation" )
    orgCode = next( ( k for k,d in codio.get_organisation_details().items() if d["name"] == "Coventry University" ), None )

    for username, uid in codio.get_students( orgCode ):
        try:
            details = codio.get_account_details( username )
        except ValueError: 
            logger.debug( f"{username} not active" )
            continue # user not active

        yield details

    return
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger( "__main__" ).setLevel( logging.DEBUG )

    logger = logging.getLogger(__name__)
    logger.debug( "Handle parameters" )

    usageTxt = "help"
    
    params = {"help": False, "user": None, "cpass": None, "pass": None, "output": "codio_report.csv"}
    shortparams = {"h":"help", "u":"user", "p":"pass", "o":"output"}
        
    # configure flags
    longopts = [ k+["","="][v==None] for k, v in params.items() ]
    shortopts = "".join([ k+["",":"][params[v]==None] for k, v in shortparams.items()])
    try:
        opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    except getopt.GetoptError as e:
        print(e)
        sys.exit(1)
        
    # process flags
    for o, a in opts:
        o = o.lstrip("-")
        if len(o) == 1: o = shortparams[o]
        if len(a)==0 and params[o] == False: params[o] = True
        else: params[o] = a
               
    if not params["user"]: params["user"] = input("username: ")
    if not params["cpass"]: params["cpass"] = getpass.getpass("codio password: ")
    if not params["pass"]: params["pass"] = getpass.getpass("uni password: ")

    main( params["user"], params["cpass"], params["pass"], params["output"] )
  
    sys.exit(0)

   