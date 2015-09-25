__author__ = 'Jiaxiao Zheng'

import cgi
import urllib

from google.appengine.ext import ndb
from google.appengine.api import users, files, images
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
import webapp2
import jinja2
import os
import re #used to parse list of emails
from google.appengine.api import mail #mailing functions in invitation, notification

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


# in this api handler, define the services for:
# management, create stream, view a stream, image upload, view all stream, search streams, and report request

# use ndb
# first define object class

class image(ndb.Model):
    owner = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add = True)
    location = ndb.GeoPtProperty(required=True, default=ndb.GeoPt(0,0))
    blob_key = ndb.BlobKeyProperty()

class stream(ndb.Model):
    name = ndb.StringProperty()
    owner = ndb.StringProperty()
    figures = ndb.StructuredProperty(image,repeated = True)
    tags = ndb.StringProperty()
    cover_url = ndb.StringProperty()
    #YW: add property to record subscribers
    subscriber = ndb.UserProperty(repeated = True

class user_subscribe(ndb.Model):
    identity = ndb.StringProperty()
    subscribed_streams = ndb.StringProperty(repeated = True)

class ViewStreamHandler(webapp2.RequestHandler):
    def get(self,id):
        PhotoUrls = []
        all_stream = stream.query()
        for siter in all_stream:
            if str(siter.key.id()) == id:
                current_stream = siter
                break

        for img in current_stream.figures:
            PhotoUrls.append(images.get_serving_url(img.blob_key))

        template_values = {'String1': current_stream.name, 'url_list': PhotoUrls}
        template = JINJA_ENVIRONMENT.get_template('view_stream.html')
        self.response.write(template.render(template_values))

class PhotoUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
       # self.redirect('/management')
        try:
            upload = self.get_uploads()[0]
            stream_name = self.request.get("stream_name")
            user_photo = image(owner=users.get_current_user().user_id(),
                                   blob_key=upload.key())

            all_stream = stream.query()
            for siter in all_stream:
                if str(siter.name) == stream_name:
                    current_stream = siter
                    siter.figures.append(user_photo)
                    print "put is being called"
                    siter.put()
                    break

          #  current_stream = stream.get_by_id(stream_id)
            #TODO: uploading still needs some timt to complete, we need to control the speed of redirect
            self.redirect('/view/%s' % siter.key.id())


        except:
            self.error(500)




class CreateStreamHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user is None:
            self.redirect("/error")
        name = self.request.get("name") #TODO: check whether name is not use
        owner = user.user_id()
        subscriber = parseSubscriber(self.request.get("subscriber")) #TODO: parser of subscriber emails
        subscribe_message = self.request.get("subscribe_message") #TODO: send emails to subscribers
        new_stream = stream(name = self.request.get("name"), owner = user.user_id(), cover_url = self.request.get("cover_url"),figures = [],tags = [])
        new_stream.put()

        self.redirect("/management")

def parseSubscriber(subscriber_string):
    "This function parse the email addresses from string"
    if subscriber_string.empty():
        return []
     
