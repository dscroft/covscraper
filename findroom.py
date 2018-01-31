import getpass, getopt
import covscraper
import datetime
import sys

if __name__ == "__main__":
    usageTxt = "help"
    
    params = {"user": None, "pass": None, "room": "", "equip": "", "course": "", "uid": "", "date": None, "for": 1.0}
    week = covscraper.timetableapi.cov_week(datetime.datetime.now())
    
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
            print(usageText)
            sys.exit(1)
        elif o in ("free",):
            params["free"] = True
        
        for p in params:
            if o in ("-{:.1}".format(p), "--{}".format(p)):
                params[p] = a

    # handle defaults
    if not params["user"]: params["user"] = input("username: ")
    if not params["pass"]: params["pass"] = getpass.getpass("password: ")
    params["equip"] = set(params["equip"].split(","))
    params["for"] = float(params["for"])

    params["date"] = datetime.datetime.strptime(params["date"], "%d/%m/%Y %H:%M") if params["date"] else datetime.datetime.now()
    params["till"] = params["date"] + datetime.timedelta(hours=params["for"])
              
    currentweek = covscraper.timetableapi.cov_week(params["date"])

    # authenticate and get the timetable
    session = covscraper.auth.Authenticator(params["user"], params["pass"])

    for room, data in covscraper.rooms.ROOMS.items():
        slots = covscraper.timetableapi.get_timetable( session, room=room)
        slots = [ s for s in slots if (s["start"] <= params["date"] and params["date"] < s["end"]) \
                                   or (s["start"] <= params["till"] and params["till"] < s["end"]) ]

        free = slots == []
        if free or "free" not in params:
            print("{} - {} - {}".format(room,("Busy","Free")[free],data["desc"]))

    sys.exit(0)
    