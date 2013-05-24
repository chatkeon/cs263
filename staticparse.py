import os
import StringIO
import inspect
import tokenize
import json
import collections
import re

def main():

    # create an ordered dictionary to hold information
    dictionary = collections.OrderedDict()

    # open configuration file
    config = open("app.yaml","r")

    # read in name of application
    line = config.readline()
    line = line.split(":")
    dictionary[ "Name" ] = line[1].strip()

    # read in description, if given
    line = config.readline()
    if (line.startswith("#")):
        line = line.split("#")
        dictionary[ "Description" ] = line[1].strip()
    else:
        dictionary[ "Description" ] = "Unspecified"
        line = line.split(":")
        dictionary[ "Version" ] = line[1].strip()

    # read in compatibility (i.e.. version of Python)
    line = config.readline()
    line = line.split(":")
    if (line[1].strip() == "python27"):
        dictionary[ "Compatibility" ] = "2.7"
    elif (line[1].strip() == "python"):
        dictionary[ "Compatibility" ] = "2.5"
    else:
        dictionary[ "Compatbility" ] = "All"

    # read in identifier
    line = config.readline()
    line = line.split(":")
    dictionary[ "Identifier" ] = line[1].strip()

    # add base URL, determined by appending ".appspot.com" to the app name
    base = dictionary[ "Name" ] + ".appspot.com"
    dictionary[ "Base" ] = base

    return dictionary

    # the remaining code was previously used to obtain app URLs;
    # that information is now obtained dynamically

    #print json.dumps(dictionary,sort_keys=False,indent=4,separators=(',', ': '))

    #line = config.readline()
    #while (not line.startswith("- url: /.*")):
        #line = config.readline()
    #line = config.readline()
    #line = line.split(":")
    #main = line[1].split(".")
    #app = main[1].strip()
    #main = main[0].strip()
    #main = main + ".py"
    #file = open(main,"r")
    #line = file.readline()
    #while (not line.startswith(app)):
        #line = file.readline()

    #end = []
    #end.append(line.strip())
    #for line in file:
        #end.append(line.strip())

    #urls = ""
    #for i in end:
        #urls = urls + str(i).lstrip()

    #urls = re.sub(r'\s+', '', urls)
    #urls = urls.split(",")
    #size = len(urls)

    # obtain path information for each class
    # enter information into class
    # path is indexed by class name
    #i = 1
    #while (i < size):
        #if (i == 1):
            #dictionary[ str((urls[i].split(")"))[0]) ] = str((urls[i-1].split("("))[2])
        #else:
            #dictionary[ str((urls[i].split(")"))[0]) ] = str((urls[i-1].split("("))[1])
        #i = i + 2

    #return dictionary