# For Daniel's Phd project, will generate the mapping between the 
# anonymous ids that he has and the student ids that the university uses

import getpass, getopt
import codioscraper
import sys
import logging
import covscraper
import hashlib

def main( user, cpass, upass ):
    logger = logging.getLogger(__name__)

    logger.info( "Connect to Aula" )
    session = covscraper.auth.Authenticator( user, upass )

    for user in get_codio_users( user, cpass ):
        anonyId = hashlib.sha256( user["username"].encode() ).hexdigest()
        sid = covscraper.aulaapi.email_to_id( session, user["email"] )

        print( f"{anonyId},{sid},{user['email']}" )

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
    
    params = {"help": False, "user": None, "cpass": None, "pass": None}
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
    if not params["cpass"]: params["cpass"] = getpass.getpass("codio password: ")
    if not params["pass"]: params["pass"] = getpass.getpass("uni password: ")

    main( params["user"], params["cpass"], params["pass"] )
  
    sys.exit(0)

   
