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
from datetime import *
import time
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

class view_counter(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add = True)

class stream(ndb.Model):
    name = ndb.StringProperty()
    owner = ndb.StringProperty()
    figures = ndb.StructuredProperty(image,repeated = True)
    tags = ndb.StringProperty(repeated = True)
    cover_url = ndb.StringProperty()
    #TODO: the num_of_view should be calculated by a queue, if a view is outdated, it should be removed
    views = ndb.StructuredProperty(view_counter,repeated = True)
    num_of_view = ndb.IntegerProperty()

class trend_subscribers(ndb.Model):
    user_email = ndb.StringProperty()
    report_freq = ndb.IntegerProperty()



class ViewStreamHandler(webapp2.RequestHandler):
    def get(self,id):
        print("stream viewing")
        PhotoUrls = []
        all_stream = stream.query()
        current_stream = stream.get_by_id(int(id))
        current_stream.num_of_view += 1
        now_time = view_counter()
        now_time.put()
        current_stream.views.append(now_time)
        cutofftime = datetime.now() - timedelta(minutes=1)
        delete_list = [] # if directly deleting elements in views, the range of for loop will be variable, out_of_bound occurs
        for i in range(0,len(current_stream.views)):
            if datetime.now()-current_stream.views[i].date > timedelta(minutes = 1):
                #for now let's say the record only keep for 1 mins
                current_stream.views.remove(current_stream.views[i])
            else:
                break


        current_stream.num_of_view = len(current_stream.views)
        current_stream.put()

      #  nviews = Num_Of_Views[id]
        for img in current_stream.figures:
            PhotoUrls.append(images.get_serving_url(img.blob_key))

        template_values = {'String1': current_stream.name, 'url_list': PhotoUrls, 'nviews':current_stream.num_of_view}
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
            all_stream = stream.query()
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
            self.redirect("/error")

        new_stream = stream(name = self.request.get('name'), owner = user.user_id(), cover_url = self.request.get('cover_url'),tags=[], figures = [],views = [], num_of_view = 0)
        #new_stream = stream(name = 'test', owner = user.user_id(), cover_url = 'test_url',tags=[], figures = [])

        new_key = new_stream.put()
     #   Num_Of_Views[str(new_key.id())] = 0

        self.redirect("/management")

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