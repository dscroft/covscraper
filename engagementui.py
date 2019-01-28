import getpass, getopt
import covscraper
import datetime
import sys, json
import multiprocessing as mp

class Processor:
  def __init__(self, credentials, module=None, since=None, till=None, latest=None):
    self.sessions = {}
    self.credentials = credentials
    self.module = module
    self.since = since
    self.till = till
    self.latest = latest

  def get_session(self):
    pid = mp.current_process().name
    if pid not in self.sessions:
      self.sessions[pid] = covscraper.auth.Authenticator( *self.credentials )

    return self.sessions[pid]

  def __call__(self, uid):
    engagement = covscraper.studentapi.get_engagement( self.get_session(), uid )
    
    if self.module: engagement["sessions"] = [ s for s in engagement["sessions"] if s["module"] == self.module ]
    if self.since: engagement["sessions"] = [ s for s in engagement["sessions"] if s["start"] >= self.since ]
    if self.till: engagement["sessions"] = [ s for s in engagement["sessions"] if s["start"] <= self.till ]

    attendance, _ = covscraper.studentapi.get_attendance( engagement, self.latest )

    return uid, attendance


if __name__ == "__main__":
    usageTxt = "help"
    
    user = None
    pwd = None
    module = None
    till = None
    since = None
    workers = 20
    latest = False
   
    # configure flags
    shortopts = "u:p:m:t:s:w:lh"
    longopts = ["user=","pass=","module=","till=","since=","workers=","help","latest"]
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
        elif o in ("-l", "--latest"): latest = True
        elif o in ("-u", "--user"): user = a
        elif o in ("-p", "--pass"): pwd = a
        elif o in ("-m", "--module"): module = a
        elif o in ("-t", "--till"): till = datetime.datetime.strptime(a, "%d/%m/%Y")
        elif o in ("-s", "--since"): since = datetime.datetime.strptime(a, "%d/%m/%Y")
        elif o in ("-w", "--workers"): workers = int(a)

    if not user: user = input("username: ")
    if not pwd: pwd = getpass.getpass("password: ")
    
    # get student uids
    students = args + sys.stdin.readlines()
    students = [ int(i) for i in students ]

    # get engagement data
    process = Processor( (user, pwd), 
                module=module, since=since, till=till, latest=latest )

    print("uid, ontime, late, attended, absent")
    with mp.Pool( processes=workers ) as pool:
        for student, attendance in pool.imap_unordered( process, students ):

            if attendance == None:
                print(student)

            print( "{student}, {ontime}, {late}, {attended}, {absent}".format(student=student,
                                                                              ontime=attendance["On Time"],
                                                                              late=attendance.get("late",0),
                                                                              attended=attendance["Attended"],
                                                                              absent=attendance["Absent"]) )
            sys.stdout.flush()

    sys.exit(0)
   