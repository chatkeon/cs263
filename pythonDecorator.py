import os
import StringIO
import inspect
import tokenize
import json
import collections
import webapp2
import staticparse

from functools import wraps
from google.appengine.ext.webapp import Response

flag = 0
processed = []
classlist = []
resources = []
dictionary = collections.OrderedDict()
dataTypes = []

def description(fn):
    """
    A decorator that prints the name of the class of a bound function (IE, a method).

    NOTE: This MUST be the first decorator applied to the function! E.g.:

    @another_decorator
    @yet_another_decorator
    @print_class_name
    def my_fn(stuff):
    pass

    This is because decorators replace the wrapped function's signature.
    """
    global processed
    global dictionary
    global flag
    global dataTypes
    global classlist
    global resources

    # run staticparse.py at the very beginning
    if (flag == 0):
        dictionary = staticparse.main()
        flag = 1

    if (not inspect.isclass(fn)):
        @wraps(fn)
        def inner(*args, **kwargs):
            args_map = {}
            if args or kwargs:
                args_map = inspect.getcallargs(fn, *args, **kwargs)
            docstring = fn.__doc__
            # We assume that if an argument named `self` exists for the wrapped
            # function, it is bound to a class, and we can get the name of the class
            # from the 'self' argument.
            print "**************************************"

            # if 'self' in args_map:
            # check for inputBindings here
            cls = args_map['self'].__class__
            checkproc = fn.__name__ + cls.__name__

            if (checkproc not in processed):

                processed.append(checkproc)

                if (cls.__name__ not in classlist):
                    operations = []
                    classlist.append(cls.__name__)
                else:
                    # find class in list of resources
                    for i in (dictionary[ "Resources" ]):
                        if (i[ "Name" ] == cls.__name__):
                            operations = i[ "Operations" ]
                            break

                classdict = collections.OrderedDict()
                classdict[ "Name" ] = cls.__name__
                classdict[ "Path" ] = args_map['self'].request.path

                methoddict = collections.OrderedDict()

                #methoddict[ "Name" ] = fn.__name__
                #methoddict[ "Class" ] = cls.__name__

                #if not (cls.__name__ in classlist):
                    #classlist.append(cls.__name__)
                    #classdict = parseclassdoc(cls)
                    #resources.append(classdict)
                    #dictionary[ "resources" ] = resources

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

                docdict = parsefunctiondoc(docstring)
                # print "Arguments? ", docdict[ "Arguments" ]
                methoddict[ "Description" ] = docdict[ "Description" ]

                print "Parameters? Maybe? ", args_map['self'].request.params

                if (methoddict[ "Method" ] != "None"):
                    # print "Request? ", args_map['self'].request
                    query = args_map['self'].request.query_string

                    if (query != ""):

                        if "Resources" in dictionary:
                            for i in (dictionary[ "Resources" ]):
                                if (i[ "Name" ] == cls.__name__):
                                    if "InputBindings" in i:
                                        inputbindings = i[ "InputBindings" ]
                                    else:
                                        inputbindings = []
                                else:
                                    inputbindings = []
                        else:
                            inputbindings = []

                        bindingdict = collections.OrderedDict()
                        query = query.split("=")
                        query = query[0].strip()
                        bindingdict[ "ID" ] = query + "IdBinding"
                        bindingdict[ "Mode" ] = "url"
                        bindingdict[ "Name" ] = query
                        type = ""
                        for i in (docdict[ "Arguments" ]):
                            if (i[ "Name" ] == query):
                                type = i[ "Type" ]
                                des = i[ "Description" ]
                        if (type == ""):
                            type = "Unknown"
                            des = "Unknown"
                        bindingdict[ "Type" ] = type
                        bindingdict[ "Description" ] = des
                        inputbindings.append(bindingdict)
                        classdict[ "InputBindings" ] = inputbindings

                    # print "Method? ", args_map['self'].request.method
                    req = str(args_map['self'].request)
                    req = req.split('\n')

                    for i in req:
                        if i.startswith('Content-Type: '):
                            inputtype = i.split(';')
                            break

                    inputtype = inputtype[0].split(' ')
                    inputtype = inputtype[1].strip()
                    if (inputtype != ""):
                        inputdict = collections.OrderedDict()
                        inputdict[ "Content type" ] = inputtype
                        inputdict[ "Type" ] = docdict[ "Arguments" ]
                        methoddict[ "Input" ] = inputdict
                    elif (query != ""):
                        inputdict = collections.OrderedDict()
                        params = []
                        paramdict = collections.OrderedDict()
                        paramdict[ "binding" ] = query
                        params.append(paramdict)
                        inputdict[ "Params" ] = params
                        methoddict[ "Input" ] = inputdict

                    outputdict = collections.OrderedDict()

                    # print "Response? ", args_map['self'].response
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
                    methoddict[ "Output" ] = outputdict
                    methoddict[ "Errors" ] = docdict[ "Errors" ]

                    operations.append(methoddict)
                    classdict[ "Operations" ] = operations
                    resources.append(classdict)
                    dictionary[ "Resources" ] = resources
                    print json.dumps(dictionary,indent=4,separators=(',', ': '))
                    print "**************************************"

            return fn(*args, **kwargs)
        return inner
    #else:
        #if (not fn.__name__ in classlist):
            #classlist.append(fn.__name__)
            #classdict = parseclassdoc(fn)
            #dataTypes.append(classdict)
            #dictionary[ "dataTypes" ] = dataTypes
        #print "Class list: ", classlist
        #print "**************************************"
        #print json.dumps(dictionary,indent=4,separators=(',', ': '))
        #print "**************************************"
        #return fn

def parsefunctiondoc(docstring):
    docdict = collections.OrderedDict()
    if (docstring == None):
        docdict[ "Description" ] = "Unspecified"
        docdict[ "Arguments" ] = "Unspecified"
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict
    docstring = docstring.split("\n")
    docsize = len(docstring)
    if (docsize == 1):
        docdict[ "Description" ] = docstring[0].strip()
        docdict[ "Arguments" ] = "Unspecified"
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict
    docsize = docsize - 1
    description = ""
    i = 0
    while(i<docsize and (not (docstring[i].strip()).startswith("Args"))):
        description = description + str(docstring[i].strip()) + " "
        i = i + 1
    docdict[ "Description" ] = description.strip()
    if (i == docsize):
        docdict[ "Arguments" ] = "Unspecified"
        docdict[ "Returns" ] = "Unspecified"
        docdict[ "Errors" ] = "Unspecified"
        return docdict
    arguments = []
    i = i + 1
    while(i<docsize):
        argline = docstring[i].split(":")
        if (len(argline) == 1):
            break
        else:
            argdict = collections.OrderedDict()
            argdict[ "Name" ] = str(argline[0].strip())
            argdict[ "Type" ] = str(argline[1].strip())
            if (len(argline) == 3):
                argdict[ "Description" ] = str(argline[2].strip())
            else:
                argdict[ "Description" ] = "Unspecified"
        arguments.append(argdict)
        i = i + 1
    docdict[ "Arguments" ] = arguments
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
    returns = ""
    i = i + 1
    while(i<docsize):
        retline = docstring[i].split(":")
        if (len(retline) == 1):
            break
        else:
            returns = returns + str(retline[1].strip())
        i = i + 1
    docdict[ "Returns" ] = returns
    if (i == docsize):
        docdict[ "Errors" ] = "Unspecified"
        return docdict
    while(i<docsize and (not (docstring[i].strip()).startswith("Exceptions"))):
        i = i+1
    if (i == docsize):
        docdict[ "Errors" ] = "Unspecified"
        return docdict
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
        errors.append(errdict)
        i = i + 1
    docdict[ "Errors" ] = errors
    return docdict

def parseclassdoc(classobj):
    docstring = classobj.__doc__
    classdict = collections.OrderedDict()
    classdict[ "Name" ] = classobj.__name__
    global dataTypes
    if (docstring == None):
        classdict[ "Description" ] = "Unspecified"
        classdict[ "Fields" ] = "Unspecified"
        dataTypes.append(classdict)
        return
    docstring = docstring.split("\n")
    docsize = len(docstring)
    if (docsize == 1):
        classdict[ "Description" ] = docstring[0].strip()
        classdict[ "Fields" ] = "Unspecified"
        dataTypes.append(classdict)
        return
    docsize = docsize - 1
    description = ""
    i = 0
    while(i<docsize and (not (docstring[i].strip()).startswith("Attributes"))):
        description = description + str(docstring[i].strip()) + " "
        i = i + 1
    classdict[ "Description" ] = description.strip()
    if (i == docsize):
        classdict[ "Fields" ] = "Unspecified"
        dataTypes.append(classdict)
        return
    fields = []
    i = i + 1
    while(i<docsize-1):
        fielddict = collections.OrderedDict()
        argline = docstring[i].split(":")
        if (len(argline) == 1):
            fielddes = "Unspecified"
        else:
            fielddes = argline[1].strip()
        argline = argline[0].split()
        fielddict[ "Name" ] = argline[1].strip()
        fielddict[ "Description" ] = fielddes
        fielddict[ "Type" ] = argline[0].strip()
        fields.append(fielddict)
        i = i + 1
    classdict[ "Fields" ] = fields
    return classdict