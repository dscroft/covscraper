import covscraper
import sys
from bs4 import BeautifulSoup
import re

session = covscraper.auth.Authenticator("ac0745",sys.argv[1])

i = 0
blank = 0
while blank < 100:
  title = covscraper.moodleapi.get_module_name( session, i )
  if title == None:
    blank += 1
  else:
    blank = 0
    print( f"{i}|{title}" )
  
  i += 1
