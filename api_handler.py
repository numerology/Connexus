__author__ = 'Jiaxiao Zheng'

import cgi
import urllib

from google.appengine.ext import ndb
from google.appengine.api import users, files, images
import webapp2

# in this api handler, define the services for:
# management, create stream, view a stream, image upload, view all stream, search streams, and report request

# use ndb
# first define object class

class image(ndb.Model):
    owner = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add = True)
    location = ndb.StringProperty(required=True, default=ndb.GeoPt(0,0))

class stream(ndb.Model):
    name = ndb.StringProperty()
    owner = ndb.StringProperty()
    images = ndb.StructuredProperty(image,repeated = True)
    cover_url = ndb.StringProperty()

class ListStreamHandler(webapp2.RequestHandler):
    def get(self):
        stream_list = stream.query()



class CreateStreamHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()

        new_stream = stream(name = self.request.get("name"), owner = user.user_id(), cover_url = self.request.get("cover_url"),images = [])
        new_stream.put()

        self.redirect("/management")