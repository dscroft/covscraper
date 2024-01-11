import covscraper
import pickle
import sys
import codioscraper, re



session = covscraper.auth.Authenticator("ac0745",sys.argv[1])

grades = covscraper.moodleapi.get_grades( session, 47297 )
students = grades.keys()


for i in students:
	print(i)