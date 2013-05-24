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