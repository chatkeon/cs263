#from __future__ import with_statement

import os
import sys
import StringIO
import inspect
import tokenize
import json
import collections
import webapp2
import staticparse

from functools import wraps
from google.appengine.ext.webapp import Response
from google.appengine.ext import blobstore
from google.appengine.api import files
from google.appengine.api import memcache
from webapp2_extras import json

# declare and initialize global variables
flag = 0
processed = []
classlist = []
resources = []
datatypes = []
types = []
validtypes = [ "bool", "boolean", "none", "type", "int", "long", "float", "complex",
                "str", "string", "unicode", "tuple", "list", "dict", "dictionary",
                "function", "lambda", "generator", "code", "class", "instance",
                "method", "unbound method", "builtinfunction", "builtinmethod",
                "module", "file", "xrange", "slice", "ellipsis", "traceback",
                "frame", "buffer", "dictproxy", "notimplemented", "getsetdescriptor",
                "memberdescriptor" ]
dictionary = collections.OrderedDict()
errorcodes = []
#blobkey = 0

def description(fn):

    global processed
    global dictionary
    global flag
    global datatypes
    global validtypes
    global types
    global classlist
    global resources
    global errorcodes
    #global blobkey

    # start with information from the configuration file app.yaml
    # obtained by running staticparse.py exactly once
    if (flag == 0):
        dictionary = staticparse.main()

        #api = files.blobstore.create(mime_type='application/octet-stream')
        #with files.open(api, 'a') as f:
            #f.write('data')
        #files.finalize(api)
        #blobkey = files.blobstore.get_blob_key(api)

        #api = blobstore.BlobInfo.get(blobkey)
        #print "File? ", api.filename

        flag = 1

    # the decorated object is a method
    if (not inspect.isclass(fn)):
        @wraps(fn)
        def inner(*args, **kwargs):
            args_map = {}
            if args or kwargs:
                args_map = inspect.getcallargs(fn, *args, **kwargs)
            docstring = fn.__doc__

            #print "**************************************"

            # obtain the name of the method's class
            cls = args_map['self'].__class__
            checkproc = fn.__name__ + cls.__name__

            # check to see if this method is in the description yet
            if (checkproc not in processed):

                # add method to list of processed methods
                processed.append(checkproc)

                update = 0

                # add the method to the class's list of operations
                # if the class is not in the classlist, add it
                # if there are other operations already listed, update operations
                if (cls.__name__ not in classlist):
                    operations = []
                    classlist.append(cls.__name__)
                else:
                    # find class in list of resources
                    for i in (dictionary[ "Resources" ]):
                        if (i[ "Name" ] == cls.__name__):
                            update = 1
                            operations = i[ "Operations" ]
                            break

                # create a dictionary to hold the class's information
                # obtain name and path of class
                classdict = collections.OrderedDict()
                classdict[ "Name" ] = cls.__name__
                classdict[ "Path" ] = args_map['self'].request.path

                # create a dictionary to hold the method's information
                methoddict = collections.OrderedDict()

                #methoddict[ "Name" ] = fn.__name__
                #methoddict[ "Class" ] = cls.__name__

                #if not (cls.__name__ in classlist):
                    #classlist.append(cls.__name__)
                    #classdict = parseclassdoc(cls)
                    #resources.append(classdict)
                    #dictionary[ "resources" ] = resources

                # obtain http method
                if (fn.__name__ == "get"):
                    methoddict[ "Method" ] = "GET"
                elif (fn.__name__ == "post"):
                    methoddict[ "Method" ] = "POST"
                elif (fn.__name__ == "put"):
                    methoddict[ "Method" ] = "PUT"
                elif (fn.__name__ == "head"):
                    methoddict[ "Method" ] = "HEAD"
                elif (fn.__name__ == "options"):
                    methoddict[ "Method" ] = "OPTIONS"
                elif (fn.__name__ == "delete"):
                    methoddict[ "Method" ] = "DELETE"
                elif (fn.__name__ == "trace"):
                    methoddict[ "Method" ] = "TRACE"
                else:
                    methoddict[ "Method" ] = "None"

                # parse the docstring for given information
                docdict = parsefunctiondoc(docstring)

                print "Arguments? ", docdict[ "Arguments" ]

                # obtain the method's description from the docstring
                methoddict[ "Description" ] = docdict[ "Description" ]

                print "Parameters? Maybe? ", args_map['self'].request.params

                # check to ensure the method is an http method
                if (methoddict[ "Method" ] != "None"):

                    # obtain and parse http request for queries
                    print "Request? ", args_map['self'].request
                    query = args_map['self'].request.query_string
                    query = query.split("=")
                    query = query[0].strip()

                    # check for input bindings, as specified in the docstring
                    if (docdict[ "Bindings" ] != "Unspecified"):

                        inputbindings = []

                        # update inputbindings, if some have already been given
                        if "Resources" in dictionary:
                            for i in (dictionary[ "Resources" ]):
                                if (i[ "Name" ] == cls.__name__):
                                    if "InputBindings" in i:
                                        inputbindings = i[ "InputBindings" ]

                        for i in (docdict[ "Bindings" ]):
                            if (i not in inputbindings):
                                inputbindings.append(i)

                        #bindingdict = collections.OrderedDict()
                        #bindingdict[ "ID" ] = query + "Binding"
                        #bindingdict[ "Mode" ] = "url"
                        #bindingdict[ "Name" ] = query
                        #type = ""
                        #if (docdict[ "Arguments" ] != "Unspecified"):
                            #for i in (docdict[ "Arguments" ]):
                                #if (i[ "Name" ] == query):
                                    #type = i[ "Type" ]
                                    #des = i[ "Description" ]
                                    #del i
                                    #break
                        #if (type == ""):
                            #type = "Unknown"
                            #des = "Unknown"
                        #bindingdict[ "Type" ] = type
                        #bindingdict[ "Description" ] = des

                        classdict[ "InputBindings" ] = inputbindings

                    # parse http request for inputs
                    #print "Method? ", args_map['self'].request.method
                    req = str(args_map['self'].request)
                    req = req.split('\n')

                    inputtype = []
                    for i in req:
                        if i.startswith('Content-Type: '):
                            inputtype = i.split(';')
                            break

                    # check for and parse input information (bindings, queries, etc.)
                    # types and descriptions are obtained from the docstring
                    if (inputtype != [] or query != "" or docdict[ "Bindings" ] != "Unspecified"):
                        inputs = []

                        # create an ordered dictionary for the method's input(s)
                        inputdict = collections.OrderedDict()
                        params = []
                        if (docdict[ "Bindings" ] != "Unspecified"):
                            for i in (docdict[ "Bindings" ]):
                                paramdict = collections.OrderedDict()
                                paramdict[ "Binding" ] = i[ "ID" ]
                                params.append(paramdict)
                        if (query != ""):
                            paramdict = collections.OrderedDict()
                            paramdict[ "Mode" ] = "query"
                            paramdict[ "Name" ] = query

                            type = ""
                            if (docdict[ "Arguments" ] != "Unspecified"):
                                for i in (docdict[ "Arguments" ]):
                                    if (i[ "Name" ] == query):
                                        type = i[ "Type" ]
                                        des = i[ "Description" ]
                                        (docdict[ "Arguments" ]).remove(i)
                                        break

                            print "Doc string? ", docdict[ "Arguments" ]

                            if (type == ""):
                                type = "Unspecified"
                                des = "Unspecified"

                            paramdict[ "Type" ] = type

                            if (type not in types):
                                types.append(type)

                            paramdict[ "Description" ] = des
                            params.append(paramdict)
                        if (params != []):
                            inputdict[ "Params" ] = params
                            inputs.append(inputdict)
                        if (inputtype != []):
                            inputtype = inputtype[0].split(' ')
                            inputtype = inputtype[1].strip()
                            if (inputtype != ""):
                                inputdict = collections.OrderedDict()
                                inputdict[ "Content type" ] = inputtype
                                if (len(docdict[ "Arguments" ]) != 1):
                                    errorcodes.append(100)

                                inputargs = (docdict[ "Arguments" ])[0]
                                inputdict[ "Type" ] = inputargs[ "Type" ]

                                if (inputdict[ "Type" ] not in types):
                                    types.append(inputdict[ "Type" ])

                                inputs.append(inputdict)

                        methoddict[ "Input" ] = inputs

                    # create an ordered dictionary for the method's output
                    outputdict = collections.OrderedDict()

                    print "Response? ", args_map['self'].response

                    # obtain and parse http response
                    resp = str(args_map['self'].response)
                    resp = resp.split('\n')

                    outputtype = []
                    for i in resp:
                        if i.startswith('Content-Type: '):
                            outputtype = i.split(';')
                            break

                    # check for and parse output information
                    # types and descriptions are obtained from the docstring
                    if (outputtype != ""):
                        resp = args_map['self'].response
                        code = str(resp).split(' ')
                        status = code[0]
                        outputdict[ "Status" ] = status
                        header = resp.headers
                        outputtype = str(header).split(';')
                        outputtype = outputtype[0].split(':')
                        outputtype = outputtype[1].strip()
                        outputdict[ "Content type" ] = outputtype
                        outputdict[ "Type" ] = docdict[ "Returns" ]

                        if (len(docdict[ "Returns" ]) != 1):
                            errorcodes.append(200)

                        outputargs = (docdict[ "Returns" ])[0]
                        outputdict[ "Type" ] = outputargs[ "Type" ]

                        if (outputdict[ "Type" ] not in types):
                            types.append(outputdict[ "Type" ])

                        #if (resp.location != None):
                            #headerdict = collections.OrderedDict()
                            #headerdict[ "Name" ] = "Location"
                            #headerdict[ "Type" ] = "href"
                            #headerdict[ "Ref" ] = str(resp.location)
                            #outputdict[ "Headers" ] = headerdict
                        #else:
                            #outputdict[ "Headers" ] = "None"
                        methoddict[ "Output" ] = outputdict

                    # if errors are specified, include the error information
                    if (docdict[ "Errors" ] != "Unspecified"):
                        methoddict[ "Errors" ] = docdict[ "Errors" ]

                    # add method to the class's list of operations
                    operations.append(methoddict)
                    classdict[ "Operations" ] = operations

                    # if necessary, update the list of resources
                    if (update == 0):
                        resources.append(classdict)

                    # update the main dictionary
                    dictionary[ "Resources" ] = resources
                    dictionary[ "DataTypes" ] = datatypes

                    # obtain the blobkey for the API description
                    data = memcache.get("apidescription")

                    # check to see if an API description exists yet
                    if (data is not None):
                        memcache.replace(key="apidescription", value=dictionary, time=3600)
                        #print "Rewrote here"
                    else:
                        memcache.add(key="apidescription", value=dictionary, time=3600)
                        #print "Added"

                    #print data
                    #print json.dumps(dictionary,indent=4,separators=(',', ': '))
                    #api = blobstore.BlobInfo.get(blobkey)
                    #with files.open(api.filename, 'a') as f:
                    #    f.write(data)
                    #files.finalize(api.filename)
                    # print "**************************************"

            return fn(*args, **kwargs)
        return inner
    # the decorated object is a method-less class
    else:
        # check to see if the class has been processed yet
        if (not fn.__name__ in classlist):

            # add the class to the classlist
            classlist.append(fn.__name__)

            # parse the class's docstring for its information
            datatypedict = parsedatatypedoc(fn)

            # add the class to the list of datatypes
            datatypes.append(datatypedict)

            # update the main dictionary
            dictionary[ "Resources" ] = resources
            dictionary[ "DataTypes" ] = datatypes

        #print "Class list: ", classlist
        #print "**************************************"

        # obtain the blobkey for the API description
        data = memcache.get("apidescription")

        # check to see if an API description exists yet
        if (data is not None):
            memcache.replace(key="apidescription", value=dictionary, time=3600)
            #print "Rewrote here"
        else:
            memcache.add(key="apidescription", value=dictionary, time=3600)
            #print "Added"
        #print "**************************************"

        return fn

def parsefunctiondoc(docstring):
    global types

    # create an ordered dictionary to hold information from the docstring
    docdict = collections.OrderedDict()

    # no docstring given
    if (docstring == None):
        docdict[ "Description" ] = "Unspecified"
        docdict[ "Arguments" ] = "Unspecified"
        docdict[ "Bindings" ] = "Unspecified"
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict

    # split the docstring into lines and obtain the number of lines
    docstring = docstring.split("\n")
    docsize = len(docstring)

    # one-line docstring
    if (docsize == 1):
        docdict[ "Description" ] = docstring[0].strip()
        docdict[ "Arguments" ] = "Unspecified"
        docdict[ "Bindings" ] = "Unspecified"
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict

    # obtain information about description
    docsize = docsize - 1
    description = ""
    i = 0
    while(i<docsize and (not (docstring[i].strip()).startswith("Args"))):
        description = description + str(docstring[i].strip()) + " "
        i = i + 1
    if (description.strip() == ""):
        docdict[ "Description" ] = "Unspecified"
    else:
        docdict[ "Description" ] = description.strip()
    if (i == docsize):
        docdict[ "Arguments" ] = "Unspecified"
        docdict[ "Bindings" ] = "Unspecified"
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict

    # obtain information about argument(s), including queries
    arguments = []
    i = i + 1
    while(i<docsize):
        argline = docstring[i].split(":")
        if (len(argline) == 1):
            break
        elif (len(argline) == 2):
            argtype = argline[1].strip()
            if (argtype == ""):
                argtype = "Unspecified"
            argdes = "Unspecified"
        else:
            argtype = argline[1].strip()
            argdes = argline[2].strip()
            if (argdes == ""):
                argdes = "Unspecified"
        argdict = collections.OrderedDict()
        argdict[ "Name" ] = argline[0].strip()
        argdict[ "Description" ] = argdes
        argdict[ "Type" ] = argtype

        if (argdict[ "Type" ] not in types):
            types.append(argdict[ "Type" ])

        arguments.append(argdict)
        i = i + 1
    if (arguments == []):
        docdict[ "Arguments" ] = "Unspecified"
    else:
        docdict[ "Arguments" ] = arguments
    if (i == docsize):
        docdict[ "Bindings" ] = "Unspecified"
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict

    # obtain information about bindings
    while(i<docsize and (not (docstring[i].strip()).startswith("Bindings"))):
        description = description + str(docstring[i].strip()) + " "
        i = i + 1
    if (i == docsize):
        docdict[ "Bindings" ] = "Unspecified"
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict
    bindings = []
    i = i + 1
    while(i<docsize):
        bindline = docstring[i].split(":")
        if (len(bindline) == 1):
            break
        elif (len(bindline) == 2):
            bindtype = bindline[1].strip()
            if (bindtype == ""):
                bindtype = "Unspecified"
                binddes = "Unspecified"
                bindmode = "Unspecified"
        elif (len(bindline) == 3):
            binddes = bindline[2].strip()
            if (binddes == ""):
                binddes = "Unspecified"
                bindmode = "Unspecified"
        else:
            bindtype = bindline[1].strip()
            binddes = bindline[2].strip()
            bindmode = bindline[3].strip()
            if (bindmode == ""):
                bindmode = "Unspecified"
        binddict = collections.OrderedDict()
        binddict[ "ID" ] = bindline[0].strip() + "Binding"
        binddict[ "Mode" ] = bindmode
        binddict[ "Name" ] = bindline[0].strip()
        binddict[ "Description" ] = binddes
        binddict[ "Type" ] = bindtype

        if (binddict[ "Type" ] not in types):
            types.append(binddict[ "Type" ])

        bindings.append(binddict)
        i = i + 1
    if (bindings == []):
        docdict[ "Bindings" ] = "Unspecified"
    else:
        docdict[ "Bindings" ] = bindings
    if (i == docsize):
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict
    while(i<docsize and (not (docstring[i].strip()).startswith("Returns"))):
        i = i+1
    if (i == docsize):
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict

    # obtain information about return type
    returns = []
    i = i + 1
    while(i<docsize):
        retline = docstring[i].split(":")
        if (len(retline) == 1):
            break
        else:
            rettype = retline[1].strip()
            retdes = retline[2].strip()
            if (retdes == ""):
                retdes = "Unspecified"
        retdict = collections.OrderedDict()
        retdict[ "Name" ] = retline[0].strip()
        retdict[ "Description" ] = retdes
        retdict[ "Type" ] = rettype

        if (retdict[ "Type" ] not in types):
            types.append(retdict[ "Type" ])

        returns.append(retdict)
        i = i + 1
    if (returns == []):
        docdict[ "Returns" ] = "Unspecified"
    else:
        docdict[ "Returns" ] = returns
    if (i == docsize):
        docdict[ "Errors" ] = "Unspecified"
        return docdict
    while(i<docsize and (not (docstring[i].strip()).startswith("Exceptions"))):
        i = i+1
    if (i == docsize):
        docdict[ "Errors" ] = "Unspecified"
        return docdict

    # obtain information about errors, if given
    errors = []
    i = i + 1
    while(i<docsize):
        errdict = collections.OrderedDict()
        errline = docstring[i].split(":")
        if (errline[0].strip() == ''):
            break
        if (len(errline) == 1):
            errline = errline[0].strip()
            errdict[ "Status" ] = errline
            errdict[ "Cause" ] = Response.http_status_message(int(errline))
        else:
            errdict[ "Status" ] = errline[0].strip()
            errdict[ "Cause" ] = errline[1].strip()
        if (errdict[ "Cause" ] == ""):
            errdict[ "Cause" ] = Response.http_status_message(int(errdict[ "Status" ]))
        errors.append(errdict)
        i = i + 1
    docdict[ "Errors" ] = errors

    return docdict

def parsedatatypedoc(classobj):
    global dataTypes
    global validtypes

    # obtain the docstring
    docstring = classobj.__doc__

    # create an ordered dictionary to hold information from the docstring
    classdict = collections.OrderedDict()

    # obtain the name of the class
    classdict[ "Name" ] = classobj.__name__

    # if the class is not in the list of valid datatypes, add it
    if (classdict[ "Name" ] not in validtypes):
        validtypes.append( classdict[ "Name" ].lower() )

    # no docstring given
    if (docstring == None):
        classdict[ "Description" ] = "Unspecified"
        classdict[ "Fields" ] = "Unspecified"
        return classdict

    # split the docstring into lines and obtain the number of lines
    docstring = docstring.split("\n")
    docsize = len(docstring)

    # one-line docstring
    if (docsize == 1):
        classdict[ "Description" ] = docstring[0].strip()
        classdict[ "Fields" ] = "Unspecified"
        return classdict

    # obtain information about description
    docsize = docsize - 1
    description = ""
    i = 0
    while(i<docsize and (not (docstring[i].strip()).startswith("Attributes"))):
        description = description + str(docstring[i].strip()) + " "
        i = i + 1
    if (description.strip() == ""):
        classdict[ "Description" ] = "Unspecified"
    else:
        classdict[ "Description" ] = description.strip()
    if (i == docsize):
        classdict[ "Fields" ] = "Unspecified"
        return classdict

    # obtain information about fields
    fields = []
    i = i + 1
    while(i<docsize-1):
        fielddict = collections.OrderedDict()
        argline = docstring[i].split(":")
        if (len(argline) == 1):
            fieldtype = "Unspecified"
            fielddes = "Unspecified"
        elif (len(argline) == 2):
            fieldtype = argline[1].strip()
            if (fieldtype == ""):
                fieldtype = "Unspecified"
            fielddes = "Unspecified"
        else:
            fieldtype = argline[1].strip()
            fielddes = argline[2].strip()
            if (fielddes == ""):
                fielddes = "Unspecified"
        fielddict[ "Name" ] = argline[0].strip()
        fielddict[ "Description" ] = fielddes
        fielddict[ "Type" ] = fieldtype
        fields.append(fielddict)
        i = i + 1
    classdict[ "Fields" ] = fields

    return classdict

def validate(self):
    global types
    global validtypes
    global dictionary
    global errorcodes

    # check to see where validate function was called from
    #if (num == 100):
        #print "ERROR: Too many arguments!"
        #sys.exit()

    #if (num == 200):
        #print "ERROR: More than one return type!"
        #sys.exit()

    # check resources and operations
    if (dictionary[ "Resources" ] == []):
        errorcodes.append(1)
    else:
        for i in (dictionary[ "Resources" ]):
            if (i[ "Operations" ] == []):
                errorcodes.append(2)

    #print "Types: ", types
    #print "Valid Types: ", validtypes

    # check datatypes
    for i in types:
        if (i.lower()) not in validtypes:
            errorcodes.append(-1)
        if (i == "Unspecified"):
            errorcodes.append(-2)
        if (i == "Unknown"):
            errorcodes.append(-3)

    # if api description is valid, display it
    if (errorcodes == []):
        data = memcache.get("apidescription")
        self.response.headers['Content-Type'] = 'application/json'
        self.response.write(json.encode(data,indent=4,separators=(',', ': ')))

    # if api description is not valid, display the errors
    else:
        self.response.write(("API description was not generated.\n").replace("\n", "<br />"))
        self.response.write(("The following error(s) were found:\n").replace("\n", "<br />"))

        for i in errorcodes:
            if (i == 1):
                self.response.write(("- ERROR: No resources found.\n").replace("\n", "<br />"))
            if (i == 2):
                self.response.write(("- ERROR: Resource with no operations.\n").replace("\n", "<br />"))
            if (i == 100):
                self.response.write(("- ERROR: Incorrect number of arguments.\n").replace("\n", "<br />"))
            if (i == 200):
                self.response.write(("- ERROR: Invalid number of return types.\n").replace("\n", "<br />"))
            if (i == -1):
                self.response.write(("- ERROR: Invalid data type.\n").replace("\n", "<br />"))
            if (i == -2):
                self.response.write(("- ERROR: Information unspecified.\n").replace("\n", "<br />"))
            if (i == -3):
                self.response.write(("- ERROR: Information unknown.\n").replace("\n", "<br />"))