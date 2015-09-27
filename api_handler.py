__author__ = 'Jiaxiao Zheng'

import cgi
import urllib

from google.appengine.ext import ndb
from google.appengine.api import users, files, images
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import mail
import webapp2
import jinja2
import os
import re  # used to parse list of emails
from google.appengine.api import mail  # mailing functions in invitation, notification
import logging  # Log messages
import time

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

INVITATION_EMAIL_PLAIN_TEXT = """
%(user)s invites you to subscribe to Stream %(stream_name)s on Connexus!
%(message)s

Please go to this url: %(subscribe_stream_url)s
"""

#WEB_URL = 'connexus-yw.appspot.com'  # TODO: Change this url to the online application
WEB_URL = '/'
DEFAULT_RETURN_URL = '/management'  # Default return url for subscribe

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
    subscribers = ndb.UserProperty(repeated=True)
    tags = ndb.StringProperty(repeated=True)
    #TODO: the num_of_view should be calculated by a queue, if a view is outdated, it should be removed
    num_of_view = ndb.IntegerProperty()


class subscribe_list(ndb.Model):
    identity = ndb.StringProperty()
    subscribed_streams = ndb.StringProperty(repeated = True)


class trend_subscribers(ndb.Model):
    user_email = ndb.StringProperty()
    report_freq = ndb.IntegerProperty()


class ViewStreamHandler(webapp2.RequestHandler):
    def get(self, id):
        user = users.get_current_user()
        if user is None:
        # go to login page
            print("View Stream Handler: Not logged in")
            self.redirect(users.create_login_page(self.request.uri))
            return
        
        PhotoUrls = []
        all_stream = stream.query()
        for siter in all_stream:
            if str(siter.key.id()) == id:
                current_stream = siter
                break

        current_stream.num_of_view += 1
        current_stream.put()

      #  nviews = Num_Of_Views[id]
        for img in current_stream.figures:
            PhotoUrls.append(images.get_serving_url(img.blob_key))
            
         # TODO: Check user in this page?
      #  Add subscribe button
        """show message if owner or already subscribed; show button if not subscribed"""
        no_subscribe_message = "None"
        show_subscribe_button = True
        subscribe_return_url = self.request.uri
        if user.user_id() == current_stream.owner:
        # The user owns the stream
            print "View Stream Handler: User owns the stream, no need to subscribe"
            show_subscribe_button = False
            no_subscribe_message = "You are the owner of the Stream"
            
        already_subscribed = False  # show Already Subscribed message instead of showing a button for subscribe
        for temp_user in current_stream.subscribers:  # this for loop is used to check the id of users
            if user.user_id() == temp_user.user_id():
                already_subscribed = True
                break
        if already_subscribed:
            show_subscribe_button = False
            no_subscribe_message = "You've already subscribed to the stream" 
        
        template_values = {'String1': current_stream.name, 
                           'url_list': PhotoUrls, 
                           'nviews':current_stream.num_of_view,
                           'stream': current_stream,
                           'logout_url': users.create_logout_url('/'),
                           'no_subscribe_message': no_subscribe_message,
                           'show_subscribe_button': show_subscribe_button,
                           'subscribe_return_url': subscribe_return_url}
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
            time.sleep(1)
          #  current_stream = stream.get_by_id(stream_id)

            self.redirect('/view/%s' % siter.key.id())
        except:
            self.error(500)


class CreateStreamHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user is None:
            print 'No user'
            self.redirect("/error")
            return
        stream_name = self.request.get('name') #TODO: check whether name is not use
        if (not stream_name):
        # empty stream_name should not be allowed
            print('Stream name empty!')
            self.redirect('/error')
            return
        
        same_name_streams = stream.query(stream.name == stream_name).get()
        if (same_name_streams is not None):
            print 'Name existing, go to error page'
            self.redirect('/error')
            return
        
        owner = user.user_id()
        
        parsed_tags = parseTag(self.request.get('tag'))
        new_stream = stream(name=self.request.get('name'), owner = user.user_id(),
                            cover_url=self.request.get('cover_url'), tags=parsed_tags, figures=[], num_of_view = 0)
        # new_stream = stream(name = 'test', owner = user.user_id(), cover_url = 'test_url',tags=[], figures = [])
        new_stream.put()
        
        subscribers = parseSubscriber(self.request.get('subscriber'))
        for to_addr in subscribers:
            print to_addr
        subscribe_message = self.request.get('subscribe_message')
        invitation_email = mail.EmailMessage()
        invitation_email.sender = user.email()  # YW:sender is the creator of the stream
        invitation_email.subject = """Invitation to %(stream_name)s on Connexus from %(Invitor)s""" \
                          % {"stream_name": stream_name, "Invitor": user.nickname()}
        url_to_subscribe = (WEB_URL + '/subscribe/%s' % new_stream.key.id())
        # Print url to subscribe
        print url_to_subscribe
        template_values = {'stream_name': stream_name,
                           'subscribe_message': subscribe_message,
                           'subscribe_stream_url': url_to_subscribe}
        template = JINJA_ENVIRONMENT.get_template('subscribe_invitation_email.html')
        
        invitation_email.body = (INVITATION_EMAIL_PLAIN_TEXT % {'user': new_stream.owner,
                                                                'stream_name': new_stream.name,
                                                                'message': subscribe_message,
                                                                'subscribe_stream_url': url_to_subscribe})
        invitation_email.html = template.render(template_values)
        logging.debug(invitation_email.body)
        for to_addr in subscribers:
            if mail.is_email_valid(to_addr):
                invitation_email.to = to_addr
                invitation_email.send()

        self.redirect('/management')


class TrendReportHandler(webapp2.RequestHandler):
    def get(self, freq):
        subscriber_list = trend_subscribers.query(trend_subscribers.report_freq == int(freq))
        print "trend sending"
        for s in subscriber_list:
            cmail = mail.EmailMessage(sender = "Connexus Support <support@just-plate-107116.appspotmail.com>", subject = "Connexus Digest")
            cmail.to = s.user_email
            cmail.body = "Periodically trending msg tester."
            cmail.send()


class TrendingFrequencyHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user is None:
            self.redirect("/error")
            return

        subscriber_list = trend_subscribers.query()
        flag = False
        for s in subscriber_list:
            if s.user_email == str(user.email()):
                try:
                    s.report_freq = int(self.request.get("frequency"))
                    s.put()
                except:
                    s.report_freq = 0
                    s.put()
                flag = True
                cmail = mail.EmailMessage(sender = "Connexus Support <support@just-plate-107116.appspotmail.com>", subject = "Connexus Digest")
                cmail.to = s.user_email
                cmail.body = "You have changed your updating preference."
                cmail.send()
                break
        if(not flag):
            try:
                new_subscriber = trend_subscribers(user_email = user.email(), report_freq = int(self.request.get("frequency")))
            except:
                new_subscriber = trend_subscribers(user_email = user.email(), report_freq = 0)
            new_subscriber.put()

        self.redirect("/stream_trending")


class SubscribeStreamHandler(webapp2.RequestHandler):
    """Handle subscription to one stream"""

    def get(self, stream_id):
        """Display stream name, display cover, provide two buttons: 1)Subscribe 2)Return to return_url"""
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
            return
        return_url = self.request.get('return_url', DEFAULT_RETURN_URL)
        print ["Return URL: " + return_url]
        # YW: default return url is /management, or return to the url specified
        queried_stream = stream.get_by_id(int(stream_id))
        if queried_stream is None: # stream not found
            self.redirect('/error')
            return
            
        # YW: check whether there should be a button for subscribe
        no_subscribe_message = "None"
        show_subscribe_button = True
        if user.user_id() == queried_stream.owner:
        # The user owns the stream
            print "User owns the stream, no need to subscribe"
            show_subscribe_button = False
            no_subscribe_message = "You are the owner, no need to subscribe"
            
        already_subscribed = False  # show Already Subscribed message instead of showing a button for subscribe
        for temp_user in queried_stream.subscribers:  # this for loop is used to check the id of users
            if user.user_id() == temp_user.user_id():
                already_subscribed = True
                break
        if already_subscribed:
            show_subscribe_button = False
            no_subscribe_message = "You've already subscribed to the stream"
            
        template = JINJA_ENVIRONMENT.get_template('subscribe_temp.html')
        template_values = {'stream': queried_stream,
                           'logout_url': users.create_logout_url(WEB_URL),
                           'return_url': return_url,
                           'show_subscribe_button': show_subscribe_button,
                           'no_subscribe_message': no_subscribe_message}
        self.response.write(template.render(template_values))
        
    def post(self, stream_id):
        """Subscribe to the stream: 1.add stream to user's stream set; 2.add user to stream's subscriber list;
        3. redirect to manage page"""
        user = users.get_current_user()
        return_url = self.request.get('return_url','/')
        print ['SUBSCRIBE POST-return url: '+return_url]
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
            return
        queried_stream = stream.get_by_id(int(stream_id))
        if queried_stream is None:  # Subscribe to a non-existing stream
            self.redirect('error')
            return
        already_subscribed = False
        for temp_user in queried_stream.subscribers:  # this for loop is used to check the id of users
            if user.user_id() == temp_user.user_id():
                queried_stream.subscribers.remove(temp_user)
                queried_stream.subscribers.append(user)  # update user object
                already_subscribed = True
                break
        if not already_subscribed:
            queried_stream.subscribers.append(user)
        queried_stream.put()  # update stream
        queried_subscribe_list = subscribe_list.query(subscribe_list.identity == user.user_id()).get()
        # YW: should return at most one subscribe list
        if queried_subscribe_list is None:
            queried_subscribe_list = subscribe_list(identity=user.user_id(), subscribed_streams=[])
        queried_subscribe_list.subscribed_streams.append(queried_stream.name)
        queried_subscribe_list.put()

        self.redirect(return_url)


# Helper functions
# [Helper function for CreateStreamHandler]
def parseSubscriber(subscriber_string):
    """This function parse the email addresses from string"""
    if subscriber_string == '':
        return []
    else:
        splitter = r'[,;\t\r\n]'
        subscribers = re.split(splitter, subscriber_string)
        return subscribers
        
def parseTag(tag_string):
    """Parse tags from string"""
    tags = filter(None, re.sub('[ ,;\t\n\r]','',tag_string).split('#'))
    return tags        
        


