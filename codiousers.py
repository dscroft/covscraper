# Generate a list of current users on codio and their details

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
    logger.info( codio.get_organisation_details() )
    orgCode = next( ( k for k,d in codio.get_organisation_details().items() if d["name"] == "Coventry University" ), None )

    # === filter out accounts that were grandfathered in
    logger.info( "Get consent data" )
    #students = codio.get_ip_consent( orgCode )

    #students = { i.strip(): {} for i in sys.stdin }

    #if students == {}:
    students = { u: {"id":i} for u, i in codio.get_students( orgCode ) }

    for username in students:
        try:
            details = codio.get_account_details( username )
        except ValueError: continue # user not active

        students[username].update( details )
        print( f"{students[username]['id']}|{username}|{details['email']}|{details['name']}|{details['teacher']}")

    return
    
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger( "__main__" ).setLevel( logging.DEBUG )

    logger = logging.getLogger(__name__)
    logger.debug( "Handle parameters" )

    usageTxt = "help"
    
    params = {"help": False, "user": None, "pass": None}
    shortparams = {"h":"help", "u":"user", "p":"pass"}
        
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

   