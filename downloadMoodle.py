import getpass, getopt
import covscraper
import datetime
import sys, json, time
from bs4 import BeautifulSoup
import bs4
import os 
import urllib
import string, copy, pathlib

safechars = set(string.printable)-set(['*','"','/','\\','[',']',':',';','|','=',','])



def download_link( response, name ):
    print( "Download link", name )

    soup = BeautifulSoup( response.text, "lxml" )

    # === if it is a moodle page ===
    mainBlock = soup.find( "div", {"role": "main"} )
    if mainBlock:
        print( "  - Moodle page" )
        with open( "{}.html".format(name), "w" ) as f:
            f.write( "<html><body>" )
            f.write( str(mainBlock) )
            f.write( "</body></html>" )
        return
    
    # === not a moodle page ===
    ext = urllib.parse.urlsplit( resourceresp.url ).path.split(".")[-1]
    print( "  - {} file".format(ext) )
    if ext == "php": ext = "html"

    file = "{:02d}_{}.{}".format(filecount,name,ext)
    file = "".join([ i if i in safechars else "_" for i in file ])

    print( "  {}".format(file) )

    filepath = os.path.join( folderpath, file )
    with open( filepath, "wb" ) as f:
        f.write( resourceresp.content )

def save_image( session, tag, fullpath ):
    url = tag["src"]
    filename = urllib.parse.urlsplit( url ).path.split( "/" )[-1]


    response = session.get( url )

    with open( os.path.join(fullpath,filename), "wb" ) as f:
        f.write( response.content )

    return filename

def download_page( session, rooturl, path ):
    pageQueue = [ (rooturl, path, 6) ]
    knownpages = {}

    rootloc = urllib.parse.urlsplit( rooturl ).netloc

    while pageQueue != []:
        url, path, depth = pageQueue.pop(0)

        print()
        print( url, path )

        if url in knownpages:
            print( "  KNOWN" )
            continue

        try:
            response = session.get( url )
        except:
            print( "error getting")
            continue

        os.mkdir( path )

        soup = BeautifulSoup( response.text, "lxml" )

        # === get the content block ===
        mainBlock = soup.find( "div", {"role": "main"} )
        if not mainBlock:
            filename = urllib.parse.urlsplit( response.url ).path.split("/")[-1]
            filename = urllib.parse.unquote( filename )

            print( "  NOT A MOODLE PAGE {}".format( filename ) )

            filename = os.path.join(path, filename)
            with open( filename, "wb" ) as f:
                f.write( response.content )
                #print( ">>", f.name, filename )

            knownpages[ url ] = (filename,True)
        else:
            # === remove all hidden elements
            for tag in mainBlock.findAll( class_="accesshide" ):
                tag.decompose()

            # === remove javascript ===
            for tag in mainBlock.findAll( onclick=True ):
                del tag["onclick"]

            # === download all the images ===
            imagepath = os.path.join(path, "images")
            os.mkdir( imagepath )
            print( "|- Download images - {}".format(imagepath) )

            for img in mainBlock.findAll( "img", src=True ):
                filename = save_image( session, img, imagepath )
                print( "  |- {}".format(filename) )
                img["src"] = os.path.join( "images", filename )

            # === find all the links ===
            if depth == 1:
                print( "|- Max depth" )
            else:
                print( "|- Follow links" )
                for count, link in enumerate( mainBlock.find_all( href=True ) ):
                    parsed = urllib.parse.urlsplit( link["href"] )

                    if parsed.netloc != rootloc: continue # skip non-moodle pages

                    print( "  |- {}".format( link["href"] ) )

                    # only add safe pages
                    if parsed.path.find( "/course/view.php" ) == 0 or \
                        parsed.path.find( "/mod/url/view.php" ) == 0 or \
                        parsed.path.find( "/mod/folder/view.php" ) == 0 or \
                        parsed.path.find( "/pluginfile.php" ) == 0 or \
                        parsed.path.find( "/mod/resource/view.php" ) == 0: 
                        pass
                    else:
                        print( "  UNSAFE" )
                        continue

                    pageQueue.append( ( link["href"],
                                        os.path.join( path, "{0:03}".format(count) ),
                                        depth-1 ) )

            # === save the updated file ===
            filename = os.path.join(path, "index.html")
            with open( filename, "w" ) as f:
                f.write( "<html><body>" )
                f.write( str(mainBlock) )
                f.write( "</body></html" )

            knownpages[ url ] = (filename,False)

    del response, soup, mainBlock


    print( knownpages )

    print()
    print("Post process files")
    for filename, binary in knownpages.values():
        if binary: continue

        with open( filename, "r" ) as f:
            content = f.read()

        print( "|- {}".format(filename) )

        soup = BeautifulSoup( content, "lxml" )
        for link in soup.find_all( href=True ):
            print( "  |- {}".format(link["href"]) )
            if link["href"] not in knownpages: continue

            print( "known")

            targetfile, _ = knownpages[link["href"]]

            print( filename )
            filepath = os.path.relpath( targetfile, start=filename )

            link["href"] = str(pathlib.Path( *pathlib.Path(filepath).parts[1:] ))

        with open( filename, "w" ) as f:
            f.write( str(soup) ) 



    return 


if __name__ == "__main__":
    usageTxt = "help"
    
    params = {"user": None, "pass": None, "module": None}
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
    if not params["user"]: params["user"] = input("username: ")
    if not params["pass"]: params["pass"] = getpass.getpass("password: ")

    # get engagement data
    session = covscraper.auth.Authenticator(params["user"], params["pass"])

    section = 2
    rootdir = "download{}".format(params["module"])

    url = "https://cumoodle.coventry.ac.uk/course/view.php?id={uid}".format(uid=params["module"])
    download_page( session, url, rootdir );

    sys.exit()








    while True:
        url = "https://cumoodle.coventry.ac.uk/course/view.php?id={uid}&section={section}".format(uid=params["module"], section=section)
        response = session.get(url)
        if response.status_code == 404: break

        soup = BeautifulSoup( response.text, "lxml" )

        folderpath = "{:02d}_{}".format( section, soup.find(attrs={"class":"sectionname"}).get_text() )
        folderpath = os.path.join(rootdir,folderpath)
        print( folderpath )
        os.mkdir( folderpath )

        elems = soup.findAll("div", {"class":"activity-wrapper"})
        for filecount, e in enumerate(elems):
            try:
                if "Hidden" in e.find("span", {"class":"accesshide"}).get_text(): continue
            except AttributeError: pass

            try:
                nameElem = e.find("span", {"class":"instancename"})
                name = nameElem.find(text=True, recursive=False)
            except AttributeError: 
                # text section
                #print( "text ")

                file = "{:02d}_{}.html".format(filecount,e.get_text()[:50])
                file = "".join([ i if i in safechars else "_" for i in file ])
                filepath = os.path.join( folderpath, file )
                
                if len(e.get_text()) <= 1: continue

                print( "  {}".format(file) )

                with open( filepath, "w" ) as f:
                    f.write( "<html>"+str(e)+"</html>" )
            else:
                # link section
                link = e.find("a", href=True)["href"]

                resourceresp = session.get(link)
                resourcesoup = BeautifulSoup( resourceresp.text, "lxml" )

                # check for folder
                if resourcesoup.find("input", {"type":"submit", "value":"Download folder"}):
                    print( "folder" )

                    #for form in resourcesoup.findAll("form", action=True):
                    #    try:
                    #        downloadurl = form["action"]
                    #        downloadid = form.find("input", {"name":"id"}, value=True)["value"]
                    #        downloadkey = form.find("input", {"name":"sesskey"}, value=True)["value"]
                    #        form.find("input", {"type":"submit", "value":"Download folder"})["value"]
                    #    except TypeError: continue
                    #    else:
                    #        print(form)
                    #        headers = {"Content-Type":"application/json"}
                    #        data = {"id": downloadid, "key": downloadkey}
                    #        downloadresponse = session.post( downloadurl, data=json.dumps(data), headers=headers)
#

                    #        print(downloadresponse)
#                    print( downloadurl, downloadid, downloadkey )
#url = "https://codio.co.uk/service/"
#data = {"object":"OrganizationManager","method":"getMyOrganizations"}
#

#response = session.post( url, data=json.dumps(data), headers=headers )
#organisations = decode_organisation_data( json.loads(response.text) )


                else:
                    download_link( resourceresp, name )

                    


        section += 1
        if section > 3: break

    sys.exit(0)

   