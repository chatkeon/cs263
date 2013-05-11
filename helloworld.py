import cgi
import datetime
import urllib
import webapp2
import jinja2
import os
import pythonDecorator

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from google.appengine.ext import db
from google.appengine.api import users

@pythonDecorator.description
class Greeting(db.Model):
    """
    Models an individual Guestbook entry
    with author, content, and date.

    Attributes:
        string author: the author
        string content: the content
        DateTime date: the date and time

    """
    author = db.StringProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)

@pythonDecorator.description
def guestbook_key(guestbook_name=None):
    """
    Constructs a Datastore key for a Guestbook entity with guestbook_name.

    Args:
        guestbook_name: string
        testing: integer
        something: blah blah

    Returns:
        db.Key: key

    """
    return db.Key.from_path('Guestbook', guestbook_name or 'default_guestbook')

@pythonDecorator.description
class MainPage(webapp2.RequestHandler):
    """
    Description.
    More description.

    """

    @pythonDecorator.description
    def get(self):
        """
        Get method for class MainPage.

        Args:
            guestbook_name: string
            testing: integer
            something: blah blah

        Returns:
            db.Key: key

        Exceptions:
            404: blah blah
            500

        """
        guestbook_name=self.request.get('guestbook_name')
        greetings_query = Greeting.all().ancestor(
            guestbook_key(guestbook_name)).order('-date')
        greetings = greetings_query.fetch(10)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'greetings': greetings,
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render(template_values))

        print "URL? ", self.request.query_string

@pythonDecorator.description
class Guestbook(webapp2.RequestHandler):

    @pythonDecorator.description
    def post(self):
        """
        Here is a multi-line description.
        Blah blah blah.
        POST method for Guestbook class.

        """
        # We set the same parent key on the 'Greeting' to ensure each greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        guestbook_name = self.request.get('guestbook_name')
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = users.get_current_user().nickname()

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))


app = webapp2.WSGIApplication([('/', MainPage),
                               ('/sign', Guestbook)],
                              debug=True)