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
classlist = []
resources = []
operations = []
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
    global dictionary
    global flag
    global dataTypes
    global classlist
    global resources
    global operations

    # Run staticparse.py at the very beginning
    if (flag == 0):
        dictionary = staticparse.main()
        flag = 1

    if (not inspect.isclass(fn)):
        @wraps(fn)
        def inner(*args, **kwargs):
            methoddict = collections.OrderedDict()
            args_map = {}
            if args or kwargs:
                args_map = inspect.getcallargs(fn, *args, **kwargs)
            docstring = fn.__doc__
            # We assume that if an argument named `self` exists for the wrapped
            # function, it is bound to a class, and we can get the name of the class
            # from the 'self' argument.
            print "**************************************"
            methoddict[ "Name" ] = fn.__name__
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

            if (methoddict[ "Method" ] != "None"):
                print "Request? ", args_map['self'].request
                print "Query? ", args_map['self'].request.query_string
                print "Method? ", args_map['self'].request.method
                req = str(args_map['self'].request)
                req = req.split('\n')

                for i in req:
                    if i.startswith('Content-Type: '):
                        inputtype = i.split(';')
                        break

                inputtype = inputtype[0].split(' ')
                inputtype = inputtype[1].strip()
                if (inputtype != ""):
                    methoddict[ "Input content type" ] = inputtype

                print "Response? ", args_map['self'].response
                resp = args_map['self'].response
                code = str(resp).split(' ')
                status = code[0]
                methoddict[ "Status" ] = status
                header = resp.headers
                outputtype = str(header).split(';')
                outputtype = outputtype[0].split(':')
                outputtype = outputtype[1].strip()
                methoddict[ "Output content type" ] = outputtype

            parsefunctiondoc(docstring)
            if 'self' in args_map:
                #check for inputBindings here
                cls = args_map['self'].__class__
                methoddict[ "Class" ] = cls.__name__
                if not (cls.__name__ in classlist):
                    classlist.append(cls.__name__)
                    classdict = parseclassdoc(cls)
                    resources.append(classdict)
                    dictionary[ "resources" ] = resources
            else:
                methoddict[ "Class" ] = "None"

            if (methoddict[ "Method" ] != "None"):
                operations.append(methoddict)
            dictionary[ "operations" ] = operations
            print json.dumps(dictionary,indent=4,separators=(',', ': '))
            print "**************************************"
            return fn(*args, **kwargs)
        return inner
    else:
        if (not fn.__name__ in classlist):
            classlist.append(fn.__name__)
            classdict = parseclassdoc(fn)
            dataTypes.append(classdict)
            dictionary[ "dataTypes" ] = dataTypes
        print "Class list: ", classlist
        print "**************************************"
        print json.dumps(dictionary,indent=4,separators=(',', ': '))
        print "**************************************"
        return fn

def parsefunctiondoc(docstring):
    global dictionary
    if (docstring == None):
        dictionary[ "Description" ] = "Unspecified"
        dictionary[ "Arguments" ] = "Unspecified"
        dictionary[ "Returns" ] = "Unspecified"
        dictionary[ "Errors" ] = "Unspecified"
        return
    docstring = docstring.split("\n")
    docsize = len(docstring)
    if (docsize == 1):
        dictionary[ "Description" ] = docstring[0].strip()
        dictionary[ "Arguments" ] = "Unspecified"
        dictionary[ "Returns" ] = "Unspecified"
        dictionary[ "Errors" ] = "Unspecified"
        return
    docsize = docsize - 1
    description = ""
    i = 0
    while(i<docsize and (not (docstring[i].strip()).startswith("Args"))):
        description = description + str(docstring[i].strip()) + " "
        i = i + 1
    dictionary[ "Description" ] = description.strip()
    if (i == docsize):
        dictionary[ "Arguments" ] = "Unspecified"
        dictionary[ "Returns" ] = "Unspecified"
        dictionary[ "Errors" ] = "Unspecified"
        return
    arguments = ""
    i = i + 1
    while(i<docsize):
        argline = docstring[i].split(":")
        if (len(argline) == 1):
            break
        else:
            if (arguments == ""):
                arguments = arguments + str(argline[1].strip())
            else:
                arguments = arguments + ", " + str(argline[1].strip())
        i = i + 1
    dictionary[ "Arguments" ] = arguments
    if (i == docsize):
        dictionary[ "Returns" ] = "Unspecified"
        dictionary[ "Errors" ] = "Unspecified"
        return
    while(i<docsize and (not (docstring[i].strip()).startswith("Returns"))):
        i = i+1
    if (i == docsize):
        dictionary[ "Returns" ] = "Unspecified"
        dictionary[ "Errors" ] = "Unspecified"
        return
    returns = ""
    i = i + 1
    while(i<docsize):
        retline = docstring[i].split(":")
        if (len(retline) == 1):
            break
        else:
            returns = returns + str(retline[1].strip())
        i = i + 1
    dictionary[ "Returns" ] = returns
    if (i == docsize):
        dictionary[ "Errors" ] = "Unspecified"
        return
    while(i<docsize and (not (docstring[i].strip()).startswith("Exceptions"))):
        i = i+1
    if (i == docsize):
        dictionary[ "Errors" ] = "Unspecified"
        return
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
    dictionary[ "Errors" ] = errors

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