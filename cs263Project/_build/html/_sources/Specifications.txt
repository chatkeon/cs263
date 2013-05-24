
Specifications
==========================================================

This page gives the specifications for documenting your code, so that it is compatible with our API Description Generator.

.. _specifications:

Format of the Docstring
----------------------------------------------------------
The docstring for each method-less class should be formatted as follows::
	
	def class:

		"""
		Class description line1
		[Class description lne2]

		Attributes:
			name: type: [description]
			name: type: [description]

		"""

Everything in square brackets is optional.

The docstring for each http method should be formatted as follows::

	def httpMethod:
	
		"""
		Description line1
		[Description line2]

		Args:
			name: type: [description]
			name: type: [description]

		Bindings:
			name: type: description: binding type
			name: type: description: binding type

		Returns:
			name: type: [description]

		Exceptions:
			errorcode1: [cause]
			errorcode2: [cause]
	
		"""

Note the following:

*  Only one or two arguments are expected, where one will be the input of the http method and the other will be a query, should it exist 
*  Two types of bindings are expected, url and load balancing; these are input parameters accepted by the operations
*  Only one return type is expected; this should be the output type of the http method if it exists
*  Any http exceptions that could be raised should be specified

Again, everything in square brackets is optional.

**The category labels (Args, Bindings, Returns, and Exceptions) are mandatory. Please ensure they are there as shown above, even if the category is not applicable.**

*Bindings and exceptions can be left blank if desired.*

For an example of docstring format see the sample application at https://github.com/chatkeon/cs263 .

.. _validations:

Validation
----------------------------------------------------------------------

An API description is valid if it satisfies the following conditions:

* API has a name (has a name attribute)
* API has at least one base URL (has a base attribute pointing to a non-empty array)
* API has at least one resource (has a resources attribute pointing to a non-empty array)
* Each resource has at least one operation (each resource element has an operations attribute pointing to a non-empty array)
* Each operation has a HTTP method (each operation element has a method attribute)
* There are no references to undefined types
* There are no references to undefined input bindings

**Note that the above conditions allow for many information (fields) to be left out from an API specification. For instance all the description fields, error fields, and header fields can be left out. Also all the non-functional fields such as license, community and tags can be left out from an API specification.** [1]_

The following are the valid primitive data types:

*  bool/boolean
*  None
*  type
*  int
*  long
*  float
*  complex
*  str/string
*  unicode
*  tuple
*  list
*  dict/dictionary
*  function
*  lambda
*  generator
*  code
*  class
*  instance
*  module
*  file
*  xrange
*  slice
*  ellipsis
*  traceback
*  frame
*  buffer
*  dictproxy
*  notimplemented
*  getsetdescriptor
*  memberdescriptor

In addition to these, any instances of defined classes are considered to be valid. All other data types will invalidate the API description.

Based on the above specifications for a valid API description the following errors will be detected and displayed:

1. No resources found
2. Resource with no operations
3. Incorrect number of arguments
4. Invalid number of return types
5. Undefined data type
6. Information unspecified/unknown

The first two errors listed above probably indicate that you have not clicked through all the possible paths in your app.

.. rubric:: Footnotes
.. [1] Hiranya Jayathilaka - API Validation guidelines 
