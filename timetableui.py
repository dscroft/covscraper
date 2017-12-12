import getpass, getopt
import covscraper
import datetime
import sys

if __name__ == "__main__":
    usageTxt = "help"
    
    params = {"user": None, "pass": None, "room": "", "module": "", "course": "", "uid": "", "date": None}
    week = covscraper.timetableapi.cov_week(datetime.datetime.now())
    
    # configure flags
    shortopts = "".join(["{:.1}:".format(i) for i in params])
    longopts = ["help","students"]+["{}=".format(i) for i in params]
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
        elif o in ("-s", "--students"):
            params["students"] = True
        
        for p in params:
            if o in ("-{:.1}".format(p), "--{}".format(p)):
                params[p] = a

    # handle defaults
    params["date"] = datetime.datetime.strptime(params["date"], "%d/%m/%Y") if params["date"] else datetime.datetime.now()
        
    if not params["user"]: params["user"] = input("username: ")
    if not params["pass"]: params["pass"] = getpass.getpass("password: ")
        
    currentweek = covscraper.timetableapi.cov_week(params["date"])

    # authenticate and get the timetable
    session = covscraper.auth.Authenticator(params["user"], params["pass"])
    slots = covscraper.timetableapi.get_timetable( session, module=params["module"], room=params["room"], course=params["course"], uid=params["uid"], date=params["date"] )
    
    slots = [ covscraper.timetableapi.get_register(session,s) for s in slots if covscraper.timetableapi.cov_week(s) == currentweek ]
    
    # pretty printing
    print( "Time   - Room     - Enr -> Stu/Cap - Module" )
    for s in slots:

        try:
            capacity = int(covscraper.rooms.ROOMS[s["room"]]["size"])
        except (KeyError, TypeError):
            capacity = "?"
            
        module = s["title"].split(", ")
        module = module[0]+"..." if len(module) > 1 else module[0]    
    
        print( "{time} - {room:8} - {enrolled:3} -> {students:3}/{capacity:<3} - {module}".format(room=s["room"], \
                                                    time=s["start"].strftime("%a %H"), \
                                                    students=len(s["register"]), \
                                                    enrolled=len([i for i in s["register"] if i[3]]), \
                                                     capacity=capacity, \
                                                    module=module) )
        
        if "students" in params:
            s = covscraper.timetableapi.get_register( session, s )
            for student in s["register"]:
                print(" "+", ".join([str(i) for i in student]))


    sys.exit(0)