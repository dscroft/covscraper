import getpass, getopt
import covscraper
import datetime
import sys

if __name__ == "__main__":
    usageTxt = "help"
    
    params = {"user": None, "pass": None}
    
    # configure flags
    shortopts = "".join(["{:.1}:".format(i) for i in params])
    longopts = ["help"]+["{}=".format(i) for i in params]
    try:
        opts, args = getopt.getopt(sys.argv[1:], shortopts, longopts)
    except getopt.GetoptError as e:
        print(e)
        sys.exit(1)
        
    # process flags
    for o, a in opts:
        if o in ("-h", "--help"):
            print(usageText)
            sys.exit(1)
        
        for p in params:
            if o in ("-{:.1}".format(p), "--{}".format(p)):
                params[p] = a

    # handle defaults
    if not params["user"]: params["user"] = input("username: ")
    if not params["pass"]: params["pass"] = getpass.getpass("password: ")
        
    # authenticate and get the timetable
    session = covscraper.auth.Authenticator(params["user"], params["pass"])
    print(covscraper.kualiapi.get_module_mid(session,"4061CEM"))
    # mid = covscraper.kualiapi.get_module_mid( session, "122COM" )
    # print(mid)

    sys.exit(0)
