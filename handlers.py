from google.appengine.api import users, files, images
from google.appengine.ext import blobstore
import webapp2
import operator
from api_handler import *
from google.appengine.ext import ndb

import jinja2
import os


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)




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
        user = users.get_current_user()
        if user is None:
            self.redirect("/error")
            return
        #TODO: find the streams created by user, and streams subscribe to

        stream_owned = stream.query(stream.owner ==str(user.user_id()))

        all_stream = stream.query()
        stream_subscribed = []
        for s in all_stream:
            if user in s.subscribers:
                stream_subscribed.append(s)

        template_values = {'String1': "This is the management page",
                           'logout_url': users.create_logout_url("/"),
                           'create_url': "/stream_create",
                           'view_url': "/stream_view",
                           'search_url': "/stream_search",
                           'trending_url': "/stream_trending",
                           'list_url':"/stream_list",
                           'upload_url':"/upload_fig",
                           'stream_owned': stream_owned,
                           'stream_subscribed':stream_subscribed
                           }
        template = JINJA_ENVIRONMENT.get_template('manage_temp.html')
        self.response.write(template.render(template_values))

class CstreamHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'String1': "This is the create page",
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_create.html')
        # in create page we need a link routed to createhandler api.

        self.response.write(template.render(template_values))

class UploadHandler(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user is None:
            self.redirect("/error")

        upload_url = blobstore.create_upload_url('/upload_photo')
        template_values = {'url': upload_url}
        template = JINJA_ENVIRONMENT.get_template('upload.html')
        self.response.write(template.render(template_values))


class LstreamHandler(webapp2.RequestHandler):
    def get(self):

        user = users.get_current_user()
        if user is None:
            self.redirect("/error")
        stream_list = stream.query()
        print("running list")
        template_values = {'stream_list': stream_list,
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('list_temp.html')
        self.response.write(template.render(template_values))

class SstreamHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'String1': "This is the search page",
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_subpage.html')
        self.response.write(template.render(template_values))

class TstreamHandler(webapp2.RequestHandler):
    #trending handler
    def get(self):
        all_stream = stream.query()
        for s in all_stream:
            #clear stale views
            i = 0
            while i<len(s.views):
                print(i)
                if datetime.now()-s.views[i].date > timedelta(hours = 1):

                    s.views.remove(s.views[i])
                else:
                    break

            s.put()
        stream_list = stream.query().order(-stream.num_of_view).fetch(3)

        template_values = {'String1': "This is the trending page",
                           'stream_list': stream_list,
                           'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('temp_trending.html')
        self.response.write(template.render(template_values))

class ErrorHandler(webapp2.RequestHandler):
    def get(self):
        template_values = {'logout_url': users.create_logout_url("/")}
        template = JINJA_ENVIRONMENT.get_template('error.html')
        self.response.write(template.render(template_values))
