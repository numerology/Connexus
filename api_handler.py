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

WEB_URL = 'conexus-yw.appspt.com' #TODO: Change this url to the online application

# in this api handler, define the services for:
# management, create stream, view a stream, image upload, view all stream, search streams, and report request
# YW: and subscribe
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
    figures = ndb.StructuredProperty(image, repeated=True)
    tags = ndb.StringProperty(repeated=True)
    cover_url = ndb.StringProperty()
    #YW: add property to record subscribers
    subscribers = ndb.StringProperty(repeated=True)


class subscribe_list(ndb.Model):
    identity = ndb.StringProperty()
    subscribed_streams = ndb.StringProperty(repeated = True)


class ViewStreamHandler(webapp2.RequestHandler):
    def get(self, id):
        PhotoUrls = []
        current_stream = stream.get_by_id(int(id))
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
        if same_name_streams:
            self.redirect('/error')
        owner = user.user_id()
        
        new_stream = stream(name = self.request.get('name'), owner = user.user_id(), cover_url = self.request.get('cover_url'),tags=[], figures = [])
        # new_stream = stream(name = 'test', owner = user.user_id(), cover_url = 'test_url',tags=[], figures = [])
        new_stream.put()

        subscribers = parseSubscriber(self.request.get("subscriber")) #TODO: parser of subscriber emails
        subscribe_message = self.request.get("subscribe_message") #TODO: send emails to subscribers
        message  = mail.EmailMessage()
        message.sender = user.email() #YW: sender is the creator of the stream
        message.subject = """Invitation to %(stream_name) on Connexus from %(Invitor)s""" %{"stream_name":name, "Invitor": user.user_id()}
        url_to_subscribe = (WEB_URL + '/subscribe/%s' % new_stream.key.id())
        template_values = {'stream_name': name, 'subscribe_stream_url': url_to_subscribe}
        template = JINJA_ENVIRONMENT.get_template('subscribe_invitation.html')
        message.body = write(template.render(template_values))
        for to_addr in subscribers:
            if mail.is_email.valid(to_addr):
                message.to = to_addr
                message.send()


class SubscribeStreamHandler(webapp2.RequestHandler):
    """Handle subscription to one stream"""
    DEFAULT_RETURN_URL = '/management'

    def get(self, stream_id):
        """Display stream name, display cover, provide two buttons: 1)Subscribe 2)Return to return_url"""
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        return_url = self.request.get('return_url', DEFAULT_RETURN_URL)
        # YW: default return url is /management, or return to the url specified
        queried_stream = stream.get_by_id(int(stream_id))
        if queried_stream is None: # stream not found
            self.redirect('/error')
        template = JINJA_ENVIRONMENT.get_template('subscribe_temp.html')
        template_values = {'stream': queried_stream,
                           'logout_url': users.create_logout_url("/"),
                           'return_url': return_url}
        self.response(template.render(template_values))
        
    def post(self, stream_id):
        """Subscribe to the stream: 1.add stream to user's stream set; 2.add user to stream's subscriber list;
        3. redirect to manage page"""
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
        queried_stream = stream.get_by_id(int(stream_id))
        if queried_stream is None:  # Subscribe to a non-existing stream
            self.redirect('error')
        already_subscribed = False
        for temp_user in queried_stream.subscribers:  # this for loop is used to check the id of users
            if user.user_id() == temp_user.user_id():
                queried_stream.remove(temp_user)
                queried_stream.append(user)  # update user object
                already_subscribed = True
                break
        if not already_subscribed:
            queried_stream.append(user)
        queried_stream.put()  # update stream
        queried_subscribe_list = subscribe_list.query(subscribe_list.identity == user.user_id()).fetch(1)
        # YW: should return at most one subscribe list
        if queried_subscribe_list is None:
            queried_subscribe_list = subscribe_list(identity=user.user_id())
        queried_subscribe_list.subscribed_streams.append(stream_name)
        queried_subscribe_list.put()

        self.redirect('/management')


# Helper functions
# [Helper function for CreateStreamHandler]
def parseSubscriber(subscriber_string):
    """This function parse the email addresses from string"""
    if subscriber_string.empty():
        return []
    else:
        splitter = r'[,;\t\r\n]'
        subscribers = re.split(splitter, subscriber_string)
        return subscribers
     

