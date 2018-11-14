import getpass, getopt
import covscraper
import datetime
import sys, time
import multiprocessing as mp

def worker_init(username, password):
  import covscraper
  global _session
  _session = covscraper.auth.Authenticator(username,password)
    
def worker( uid ):
  global _session
  return uid, covscraper.studentapi.get_engagement( _session, uid )

if __name__ == "__main__":
  username = sys.argv[1]
  password = sys.argv[2]

  session = covscraper.auth.Authenticator( username, password )
  
  moodleId = 60031
  students = covscraper.moodleapi.student_ids( session, moodleId )

  print( students )

  engagement = {}

  with mp.Pool(processes=20, initializer=lambda: worker_init(username, password)) as pool:
    for count, (uid, data) in enumerate(pool.imap_unordered( worker, students )):
      engagement[uid] = data
      print( "{}/{}".format(count+1,len(students)), end="\r" )
      sys.stdout.flush()
    print()
      
  for student, data in engagement.items():
    attendance = [ (i["start"],i["status"]) for i in data["sessions"] if i["module"] == "4000CEM" ]
    attendance = sorted( attendance, key=lambda i: i[0] )
    attendance = [ i[1] for i in attendance ]
    print( student, attendance )

  
  sys.exit()

    
    