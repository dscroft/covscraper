import requests
from covscraper import auth
import datetime, sys, re
import json
import urllib
import io, csv

def _decode_csv( csvstr ):
    # extract csv data
    csvfile = io.StringIO( csvstr )
    csvdata = list( csv.reader( csvfile, delimiter=',' ) )

    # convert to dict of dicts, key is module code
    modules = {}
    for row in range(1,len(csvdata)):
        fields = { key: val for key, val in zip(csvdata[0], csvdata[row]) }           
        modules[fields["reversedCode"]] = fields["id"]

    return modules

def get_uid( session, module ):
    url = "https://coventry.kuali.co/api/v0/cm/search?status=active&index=courses_latest&q={module}"
    #url = "https://coventry.kuali.co/api/v0/cm/search/results.csv?index=courses_latest&q={module}"
    
    response = session.get(url.format(module=module))
    data=json.loads(response.text)
    # import code
    # code.interact(local=locals())
    return data[0]["id"]
    #_decode_csv( response.text ).get(module, None)

def _decode_mid( data ):
    # TODO
    return data
  
def get_module_mid( session, module ):
    url = "https://coventry.kuali.co/api/cm/courses/changes/{uid}?denormalize=true"
  
    uid = get_uid( session, module )
    print(f"Got UID: {uid}")
    response = session.get( url.format(uid=uid) )

    return _decode_mid( response.text )

