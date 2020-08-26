#!python3
import urllib.parse
import getopt, getpass
import sys, ast
import covscraper
import json
SET="2019-2020"
TYPE="lecturer"

# Who decided to send useless names back?
MATCH="Item1"
USERID="Item2"
NAME="Item3"


if __name__=="__main__":
    usageTxt = "help"   
    params = {"user": None, "pass": None, "name": "", "verbose":"False"}


    # configure flags
    shortopts = "".join(["{:.1}:".format(i) for i in params])
    longopts = ["help","free"]+["{}=".format(i) for i in params]
    try:
        opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    except getopt.GetoptError as e:
        print(e)
        sys.exit(1)
        
    # process flags
    for o, a in opts:
        if o in ("-h", "--help"):
            print(usageTxt)
            sys.exit(1)
        elif o in ("free",):
            params["free"] = True
        
        for p in params:
            if o in ("-{:.1}".format(p), "--{}".format(p)):
                params[p] = a


    #Make sure there is soemthing to search
    if len(args)==0:
        print(f"Usage:\n\n\t{sys.argv[0]} [search string]\n")
        sys.exit(1)

    lookfor=" ".join(args)
        
    # handle defaults
    if not params["user"]: params["user"] = input("username: ")
    if not params["pass"]: params["pass"] = getpass.getpass("password: ")

    params["verbose"]=ast.literal_eval(params["verbose"])        

    name=urllib.parse.quote_plus(lookfor)        
    qs=f"https://webapp.coventry.ac.uk/Timetable-main/Lookup?type={TYPE}&query={name}&setid={SET}"

    if(params["verbose"]):
        print(f"Searching for: {lookfor}")
        print(f"Query string is: {qs}")
    
    
    try:
        session = covscraper.auth.Authenticator(params["user"], params["pass"])
        response=session.get(qs)
        if params["verbose"]:
            print(f"Status code: {response.status_code}")
            
        if response.status_code==200:
            data=json.loads(response.text)
            matched=False
            for i in data:
                if i[MATCH]==0:
                    print(f"{i[USERID]}\t{i[NAME]}")
                    matched=True
            if params["verbose"] or not matched:
                print("Inexact matches:")
                for i in data:
                    if i[MATCH]!=0:
                        print(f"{i[USERID]}\t{i[NAME]}\t({i[MATCH]} distance)")

                      
        else:
            print(f"Failed to retrieve data: {response.status_code}")
        # import code
        # code.interact(local=locals())
    except covscraper.auth.AuthenticationFailure:
        print("Failed to authenticate")
        sys.exit(1)

