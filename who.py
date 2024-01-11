# takes a list of UIDs from stdin 
# gets the student details from sonic

import covscraper
import sys
import datetime


if __name__ == "__main__":
    session = covscraper.auth.Authenticator(sys.argv[1], sys.argv[2])

    now = datetime.date.today()

    print( f"uid,coursecode,coursename,year,expires")

    for uid in sys.stdin.readlines():
        uid = uid.rstrip()

        try:
            details = covscraper.studentapi.get_student_details( session, uid )
        except covscraper.studentapi.NoStudent:
            print( "{}, No student".format(uid) )
            continue

        currentCourse = sorted( details["courses"], key=lambda i: i[7] )[-1]

        #print( f"{uid},{currentCourse[0]},{currentCourse[1]},{currentCourse[4]},{currentCourse[-1].year},{currentCourse[-1].month}" ) 

        #continue

        print( f"{uid},{details['firstName']} {details['lastName']},{details['dob']},{details['gender']},{details['email']},{currentCourse}" ) 

        continue

        print( "{}, {}, {}, {}, {}, {}".format( uid, \
                                            details["email"].split("@")[0], \
                                            details["email"], \
                                            currentCourse[0], \
                                            "Past" if currentCourse[7] < now else currentCourse[4] ), currentCourse[6] )


