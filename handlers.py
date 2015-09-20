from google.appengine.api import users, files, images
from google.appengine.ext import blobstore
import webapp2
from google.appengine.ext import ndb

import jinja2
import os


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_GUESTBOOK_NAME = 'default_guestbook'




class Author(ndb.Model):
    """Sub model for representing an author."""
    identity = ndb.StringProperty(indexed=False)
    email = ndb.StringProperty(indexed=False)


class Greeting(ndb.Model):
    """A main model for representing an individual Guestbook entry."""
    author = ndb.StructuredProperty(Author)
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            self.redirect('/management')
            url = None
        else:
            url = users.create_login_url('/')
        template_values = {'login_url': url}
        template = JINJA_ENVIRONMENT.get_template('main.html')

        self.response.write(template.render(template_values))


class ManagementHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'String1': "This is the management page",
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_subpage.html')
        self.response.write(template.render(template_values))

class CstreamHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'String1': "This is the management page",
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_subpage.html')
        self.response.write(template.render(template_values))

class VstreamHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'String1': "This is the management page",
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_subpage.html')
        self.response.write(template.render(template_values))

class LstreamHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'String1': "This is the management page",
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_subpage.html')
        self.response.write(template.render(template_values))

class SstreamHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'String1': "This is the management page",
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_subpage.html')
        self.response.write(template.render(template_values))

class TstreamHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'String1': "This is the management page",
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_subpage.html')
        self.response.write(template.render(template_values))

class ErrorHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'String1': "This is the management page",
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_subpage.html')
        self.response.write(template.render(template_values))

'''
class Guestbook(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each
        # Greeting is in the same entity group. Queries across the
        # single entity group will be consistent. However, the write
        # rate to a single entity group should be limited to
        # ~1/second.
        guestbook_name = self.request.get('guestbook_name',
                                          DEFAULT_GUESTBOOK_NAME)
        greeting = Greeting(parent=guestbook_key(guestbook_name))

        if users.get_current_user():
            greeting.author = Author(
                    identity=users.get_current_user().user_id(),
                    email=users.get_current_user().email())

        greeting.content = self.request.get('content')
        greeting.put()

        query_params = {'guestbook_name': guestbook_name}
        self.redirect('/?' + urllib.urlencode(query_params))

        sender_address = "confirm@just-plate-107116.appspotmail.com"
        subject = "Confirm your registration"
        body = "test"
        mail.send_mail(sender_address,users.get_current_user().email(), subject,body)
'''
'''
class ConfirmUserSignup(webapp2.RequestHandler):
    def post(self):
        user_address = self.request.get("email_address")

        if not mail.is_email_valid(user_address):
            # prompt user to enter a valid address

        else:
            confirmation_url = createNewUserConfirmation(self.request)
            sender_address = "Example.com Support <support@example.com>"
            subject = "Confirm your registration"
            body = """
Thank you for creating an account! Please confirm your email address by
clicking on the link below:

%s
""" % confirmation_url

            mail.send_mail(sender_address, user_address, subject, body)
'''
