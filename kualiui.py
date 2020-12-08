#!/usr/bin/env python3
import getpass, getopt
import covscraper
import datetime
import sys
import json,yaml
from optparse import OptionParser

if __name__ == "__main__":
    
    usage = "usage: %prog [options] modulecode [modulecode modulecode ...]"

    parser=OptionParser(usage=usage)
    parser.add_option("-u","--user", dest="user", help="specify Kuali username", metavar="USER", default=None)
    parser.add_option("-p","--password", dest="password", help="specify Kuali password. Not recommended!", metavar="PASS", default=None)
    parser.add_option("-f","--format", dest="format", help="format for result. Valid options are: json, yaml", metavar="FORMAT", default="json", type="choice", choices=["json","yaml"])
    (options,args)=parser.parse_args()
    params = {"user": options.user, "pass": options.password}
    

    # handle defaults
    if not params["user"]: params["user"] = input("username: ")
    if not params["pass"]: params["pass"] = getpass.getpass("password: ")

    if len(args)<1:
        print("You must supply at least one module code")
        sys.exit(1)
    modules={}
    #Add auth details to session
    session = covscraper.auth.Authenticator(params["user"], params["pass"])
    for i in args:      
        mid = covscraper.kualiapi.get_module_mid(session,i)
        modules[i]=mid

    if len(args)==1: #remove dict wrapping if only one request
        modules=modules[args[0]]

    out=""
    if options.format=="json":
        out=json.dumps(modules)
    elif options.format=="yaml":
        out=yaml.dump(modules)
    else:
        print(f"Unknown format: {options.format}")
        sys.exit(1)
    print(out)
            
    sys.exit(0)
