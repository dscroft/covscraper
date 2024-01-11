# Delete accounts from codio based on their Codio username
# E.g. python3 codiodelete.py -u <username> -c <codio password> < usernames.txt

import getpass, getopt
import codioscraper
import datetime
import sys, json
import re
from itertools import islice
import logging

def main( params ):
    logger = logging.getLogger(__name__)
    
    logger.info( "Connect to codio" )
    codio = codioscraper.Codio( params["user"]+"@coventry.ac.uk", params["pass"] )

    logger.info( "Get organisation" )
    orgCode = next( ( k for k,d in codio.get_organisation_details().items() if d["name"] == "Coventry University" ), None )

    remove = set([i.strip() for i in sys.stdin.readlines()])

    logger.info( "Get student list" )
    students = { u: i for u, i in codio.get_students( orgCode ) }

    logger.info( "Removing {} accounts".format(len(remove) ) )

    for username in remove:
        try:
            print( students[username], username )
            if params["delete"]:
                # DANGER!!!
                codio._remove_student(students[username], orgCode, True)
        except KeyError:
            pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger( "__main__" ).setLevel( logging.DEBUG )

    logger = logging.getLogger(__name__)
    logger.debug( "Handle parameters" )

    usageTxt = "help"
    
    params = {"help": False, "user": None, "pass": None, "delete": False, "list": False}
    shortparams = {"h":"help", "u":"user", "c":"pass", "l":"list"}
        
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
    if not params["pass"]: params["pass"] = getpass.getpass("codio password: ")

    main( params )
  

    sys.exit(0)

   