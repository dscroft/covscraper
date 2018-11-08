import getpass, getopt
import covscraper
import datetime
import sys, time
import multiprocessing as mp
import random

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
  
    with mp.Pool(processes=20, initializer=lambda: worker_init(username, password)) as pool:
      for count, (uid, engagement) in enumerate(pool.imap_unordered( worker, students )):
        print(count, uid, engagement["year"])
      
  
    
    sys.exit()
  
  
  

    
    for count, uid in enumerate(students):
      #print( "{}/{}".format(count+1,len(students)),end="\r")
      #sys.stdout.flush()
      
      engagement = covscraper.studentapi.get_engagement( session, uid )
      print( count+1, len(students), engagement["year"])
      
    print()
    
    
    
    
    #print(student)
    
    
    
    
    