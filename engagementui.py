import getpass, getopt
import covscraper
import datetime
import sys, json

if __name__ == "__main__":
    usageTxt = "help"
    
    params = {"user": None, "pass": None, "module": None, "till": None, "from": None, "raw": None}
    week = covscraper.timetableapi.cov_week(datetime.datetime.now())
    
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
    for p in ("from","till"):
        params[p] = datetime.datetime.strptime(params[p], "%d/%m/%Y") if params[p] else None
        
    if not params["user"]: params["user"] = input("username: ")
    if not params["pass"]: params["pass"] = getpass.getpass("password: ")

    # get student uids
    students = args + sys.stdin.readlines()
    students = [ int(i) for i in students ]

    # get engagement data
    session = covscraper.auth.Authenticator(params["user"], params["pass"])

    import pickle
    rawdata = {}

    print("uid, module, ontime, late, unknown")
    for student in students:
        try:
            guages, slots = covscraper.engagementapi.get_student_engagement( session, student )
        except ValueError: 
            print( "{} does not exist on engagement system".format(student), file=sys.stderr)
            continue
        #with open("test","rb") as f:
       #     pickle.dump((guages,slots),f)
        #    guages, slots = pickle.load(f)      

        #if params["module"]: slots = [ s for s in slots if s["module"] == params["module"] ]
        if params["from"]: slots = [ s for s in slots if s["start"] >= params["from"] ]
        if params["till"]: slots = [ s for s in slots if s["start"] <= params["till"] ]

        engagement, _ = covscraper.engagementapi.get_attendance( slots )
        print("{student}, overall, {ontime}, {late}, {unknown}".format(student=student,
                                                                        ontime=engagement.get("ontime",0),
                                                                            late=engagement.get("late",0),
                                                                            unknown=engagement.get("absent",0)+engagement.get("unverified",0)))

        if params["raw"]:
            rawdata[student] = slots

        for module in set([ s["module"] for s in slots ]):
            engagement, _ = covscraper.engagementapi.get_attendance( [ s for s in slots if s["module"] == module ] )
            print("{student}, {module}, {ontime}, {late}, {unknown}".format(student=student,
                                                                            module=module,
                                                                            ontime=engagement.get("ontime",0),
                                                                            late=engagement.get("late",0),
                                                                            unknown=engagement.get("absent",0)+engagement.get("unverified",0)))

        if params["raw"]:
            with open( params["raw"], "wb" ) as f:
                pickle.dump( rawdata, f )
        
       #print(student, engagement)

    sys.exit(0)

   