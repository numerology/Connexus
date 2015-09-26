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

CREATE_INVITATION_MAIL = """
I've invited you to subscribe my new stream %(stream_name)s on Connexus!

URL: %(url)s
"""


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
    tags = ndb.StringProperty(repeated = True)
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
            user_photo.put()
            for siter in all_stream:
                if str(siter.name) == stream_name:
                    current_stream = siter
                    siter.figures.append(user_photo)
                    print "put is being called"
                    siter.put()
                    break

          #  current_stream = stream.get_by_id(stream_id)
            #TODO: uploading still needs some time to complete, we need to control the speed of redirect
            self.redirect('/view/%s' % siter.key.id())


        except:
            self.error(500)




class CreateStreamHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user is None:
            self.redirect("/error")
        name = self.request.get("name") #TODO: check whether name is not use
        same_name_streams = stream.query(stream.name == stream_name)
        if not same_name_streams:
            self.redirect('/error')
        owner = user.user_id()
        
        new_stream = stream(name = self.request.get('name'), owner = user.user_id(), cover_url = self.request.get('cover_url'),tags=[], figures = [])
        #new_stream = stream(name = 'test', owner = user.user_id(), cover_url = 'test_url',tags=[], figures = [])
        new_stream.put()
        subscribers = parseSubscriber(self.request.get("subscriber")) #TODO: parser of subscriber emails
        subscribe_message = self.request.get("subscribe_message") #TODO: send emails to subscribers
        message  = mail.EmailMessage()
        message.sender = user.email() #YW: sender is the creator of the stream
        message.subject = """Invitation to %(stream_name) on Connexus from %(Invitor)s""" %{"stream_name":name, "Invitor":}
        template_values = {'stream_name': name, 'subscribe_stream_url': url_to_subscribe}
        template = JINJA_ENVIRONMENT.get_template('subscribe_invitation.html')
        message.body = write(template.render(template_values))
        for to_addr in subscribers:
            if mail.is_email.valid(to_addr):
                message.to = to_addr
                message.send()

class SubscribeStreamHandler(webapp2.RequestHandler):
    """Handle subscription to one stream"""
    def get(self):
        """Display stream name, display cover, provide two buttons: 1)Subscribe 2)Leave"""
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        #query_params = {'stream_name': self.request.get('stream_name')}
        stream_name = self.request.get('stream_name')
        queried_stream = stream.query(stream.name == stream_name)
        if not queried_stream:
            self.redirect('/error')
        template = JINJA_ENVIRONMENT.get_template('subscribe_temp.html')
        template_values = {'stream': queried_stream,
            'logout_url': users.create_logout_url("/"),
            'return_url': "/management"}
        self.response(template.render(template_values))
        
            
        
    def post(self):
        """Subscribe to the stream: 1.add stream to user's stream set; 2.add user to stream's subscriber list;
        3. redirect to manage page"""
        user = users.get_current_user()
        if not user:
            self.redirect(users.create_login_url(self.request.uri))
        stream_name

# Helper functions
# [Helper function for CreateStreamHandler]
def parseSubscriber(subscriber_string):
    """This function parse the email addresses from string"""
    if subscriber_string.empty():
        return []
    else:
        spliter = r'[,;\t\r\n]'
        subscribers = re.split(spliter,subscriber_string)
        return subscribers
     

