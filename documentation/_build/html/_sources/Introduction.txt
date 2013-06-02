Introduction
============================================================
This tool generates API descriptions for Python web apps designed for Google App Engine. These descriptions are meant to provide an overview of the different services offered in the web apps for developers that may want to use them. They will make it easier for programmers to write code that interfaces with existing web apps.

The API descriptions are generated using a combination of Python decorators and static parsing. This requires the code to follow certain standards as listed in :ref:`validations` .

Application Requirements
-----------------------------------------------------------

In order to use this tool, a web app must satisfy the following:

* Uses webapp2 framework
* Written in Python 2.7
* Includes a valid configuration file (app.yaml)

Setup
-----------------------------------------------------------

1. Download the files *pythonDecorator.py* and *staticparse.py* from https://github.com/chatkeon/cs263
2. Add ``import pythonDecorator`` in all .py files
3. Add ``@pythonDecorator.description`` to all http methods and method-less classes; if there are other decorators, ensure that ``@pythonDecorator.description`` is the innermost one
4. Add the following class in the main .py file::

        class APIDes(webapp2.RequestHandler):
                def get(self):
                        pythonDecorator.validate(self)

5. Insert ``('/options', APIDes)`` into the list given in the ``webapp2.WSGIApplication()`` function
6. Ensure that each http method and method-less class has a docstring formatted as specified in :ref:`specifications`

**Note: Do not decorate the get method in the class APIDes.**

*Optional: Insert a one-line description of the app into app.yaml file on the line after the application name. Begin the line with "# Description: ".*

Usage
----------------------------------------------------------

In order to generate a complete API description, every http method must be invoked at least once. First click through the application until every logical path has been executed. Then add ``/options`` to the base URL to view the generated API description. If the description is not valid according to the specifications on :ref:`validations`, the error(s) found will be displayed.

**Note: If not all http methods have been invoked, an incomplete (but valid) API description may be generated.**
