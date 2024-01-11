import covscraper

if __name__ == "__main__":
    with open( "temp.html", "r" ) as f:
      covscraper.studentapi._decode_engagement( f.read() )
    
    sys.exit(0)