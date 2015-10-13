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
from time import sleep as time_sleep
import re  # used to parse list of emails
from google.appengine.api import mail  # mailing functions in invitation, notification
import logging


import random


import json


from math import ceil as connexus_ceil


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__),'../templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

INVITATION_EMAIL_PLAIN_TEXT = """
%(user)s invites you to subscribe to Stream %(stream_name)s on Connexus!
%(message)s

Please go to this url: %(subscribe_stream_url)s
"""

#WEB_URL = 'connexus-yw.appspot.com'  # TODO: Change this url to the online application
WEB_URL = 'http://just-plate-107116.appspot.com/'
DEFAULT_RETURN_URL = '/management'  # Default return url for subscribe
NDB_UPDATE_SLEEP_TIME = 0.3
MAX_IMAGE_LENGTH = 400  # max length of the images longest side

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
    external = ndb.BooleanProperty(default = False)
    ext_url = ndb.StringProperty()
    comment = ndb.StringProperty()


class view_counter(ndb.Model):
    date = ndb.DateTimeProperty(auto_now_add = True)


class stream(ndb.Model):
    name = ndb.StringProperty()
    owner = ndb.StringProperty()
    creation_time = ndb.DateTimeProperty(auto_now_add = True)
    figures = ndb.StructuredProperty(image, repeated=True)
    tags = ndb.StringProperty(repeated=True)
    cover_url = ndb.StringProperty()
    #YW: add property to record subscribers
    subscribers = ndb.UserProperty(repeated=True)

    #TODO: the num_of_view should be calculated by a queue, if a view is outdated, it should be removed
    views = ndb.StructuredProperty(view_counter,repeated = True)
    num_of_view = ndb.IntegerProperty()
    num_of_pics = ndb.IntegerProperty()
    last_modified = ndb.StringProperty()


class subscribe_list(ndb.Model):
    identity = ndb.StringProperty()
    subscribed_streams = ndb.StringProperty(repeated = True)

class user_profile(ndb.Model):
    user_id = ndb.StringProperty()
    user_email = ndb.StringProperty()
    own_streams = ndb.StringProperty(repeated=True)  # names of streams owned by user
    subscribed_streams = ndb.StringProperty(repeated=True)  # names of streams user subscribe to 

class trend_subscribers(ndb.Model):
    user_email = ndb.StringProperty()
    report_freq = ndb.StringProperty()




class ViewStreamHandler(webapp2.RequestHandler):

    def get(self, id, page):
        #Now the view is constrained to deliver 3*3 = 9 pics in a single page
        #so for the ith page, it covers from 9*(i-1) to 9*i-1
        user = users.get_current_user()
        if user is None:
        # go to login page
            print("View Stream Handler: Not logged in")
            self.redirect(users.create_login_page(self.request.uri))
            return
        if page is None:
            page = 1 #by default the 1st page



        PhotoUrls = []
        PhotoIdList = []
        # all_stream = stream.query()
        current_stream = stream.get_by_id(int(id))
        if(not current_stream):
            self.redirect("/error/" + 'Wrong stream or page number')
            return
        if not str(user.user_id()) == current_stream.owner:

            now_time = view_counter()
            now_time.put()
            current_stream.views.append(now_time)

        print("View Stream Handler: current length of views" + str(len(current_stream.views)))
        cutofftime = datetime.now() - timedelta(minutes=1)
        print(len(current_stream.views))
        delete_list = [] # if directly deleting elements in views, the range of for loop will be variable, out_of_bound occurs
        i = 0
        while i<len(current_stream.views):
            print(i)
            if datetime.now()-current_stream.views[i].date > timedelta(hours = 1):
                #for now let's say the record only keep for 1 mins
                current_stream.views.remove(current_stream.views[i])
            else:
                break


        current_stream.num_of_view = len(current_stream.views)
        current_stream.put()

      #  nviews = Num_Of_Views[id]
        npage = int(page)
        if(not current_stream.num_of_pics>9*(npage-1) and (not (current_stream.num_of_pics==0 and npage ==1))):
            self.redirect("/error/" + 'Wrong stream or page number')
            return

        for img in current_stream.figures[9*(npage-1):]:
            if(current_stream.figures.index(img) > 9*npage - 1):
                break
            if(not img.external):
                PhotoUrls.append(images.get_serving_url(img.blob_key)+"=s"+str(MAX_IMAGE_LENGTH))
            else:
                PhotoUrls.append(str(img.ext_url))
            #print(images.get_serving_url(img.blob_key))
            if(not img.external):
                PhotoIdList.append(img.blob_key)
            else: #use the timestamp as key to delete
                dtstring = str(img.date)
                dtkey = re.sub("[^0-9]", "", dtstring)
                PhotoIdList.append(dtkey)

        total_pages = int((current_stream.num_of_pics - 0.001)/9 + 1)
        print("total pages = " + str(total_pages))
        url_pages = []
        for i in range(1,total_pages+1):
            url_pages.append('/view/'+id+'/'+str(i))
            

      #  Add subscribe button
        """show message if owner or already subscribed; show button if not subscribed"""
        no_subscribe_message = "None"
        show_subscribe_button = True
        show_unsubscribe_button = False
        subscribe_return_url = self.request.uri
        unsubscribe_return_url = self.request.uri
        show_upload = False
        upload_url = blobstore.create_upload_url('/upload_photo')
        if user.user_id() == current_stream.owner:
        # The user owns the stream
            print "ViewStreamHandler: User owns the stream, no need to subscribe"
            show_subscribe_button = False
            no_subscribe_message = "You are the owner of the Stream"
            show_upload = True
        already_subscribed = False  # show Already Subscribed message instead of showing a button for subscribe
        for temp_user in current_stream.subscribers:  # this for loop is used to check the id of users
            if user.user_id() == temp_user.user_id():
                already_subscribed = True
                break
        if already_subscribed:
            show_subscribe_button = False
            show_unsubscribe_button = True
            no_subscribe_message = "You've already subscribed to the stream" 
        
        template_values = {'String1': current_stream.name, 
                           'url_list': PhotoUrls,
                           'fig_id_list': PhotoIdList,
                           'url_pages' : url_pages,
                           'num_of_pages': total_pages,
                           'nviews':current_stream.num_of_view,
                           'stream': current_stream,
                           'logout_url': users.create_logout_url('/'),
                           'no_subscribe_message': no_subscribe_message,
                           'show_subscribe_button': show_subscribe_button,
                           'show_unsubscribe_button': show_unsubscribe_button,
                           'show_upload': show_upload,
                           'upload_url':upload_url,
                           'subscribe_return_url': subscribe_return_url,
                           'unsubscribe_return_url': unsubscribe_return_url,}
        template = JINJA_ENVIRONMENT.get_template('view_stream.html')
        self.response.write(template.render(template_values))


class RefreshHandler(webapp2.RequestHandler):
    def get(self, id, page):
        #Now the view is constrained to deliver 3*3 = 9 pics in a single page
        #so for the ith page, it covers from 9*(i-1) to 9*i-1
        user = users.get_current_user()
        if user is None:
        # go to login page
            print("View Stream Handler: Not logged in")
            self.redirect(users.create_login_page(self.request.uri))
            return
        if page is None:
            page = 1 #by default the 1st page

        PhotoUrls = []
        PhotoIdList = []
        # all_stream = stream.query()
        current_stream = stream.get_by_id(int(id))



        current_stream.num_of_view = len(current_stream.views)
        current_stream.put()

      #  nviews = Num_Of_Views[id]
        npage = int(page)
        for img in current_stream.figures[9*(npage-1):]:
            if(current_stream.figures.index(img) > 9*npage - 1):
                break
            if(not img.external):
                PhotoUrls.append(images.get_serving_url(img.blob_key)+"=s"+str(MAX_IMAGE_LENGTH))
            else:
                PhotoUrls.append(str(img.ext_url))
            #print(images.get_serving_url(img.blob_key))
            if(not img.external):
                PhotoIdList.append(img.blob_key)
            else: #use the timestamp as key to delete
                dtstring = str(img.date)
                dtkey = re.sub("[^0-9]", "", dtstring)
                PhotoIdList.append(dtkey)

        total_pages = int((current_stream.num_of_pics - 0.001)/9 + 1)
        print("total pages = " + str(total_pages))
        url_pages = []
        for i in range(1,total_pages+1):
            url_pages.append('/view/'+id+'/'+str(i))


      #  Add subscribe button
        """show message if owner or already subscribed; show button if not subscribed"""
        no_subscribe_message = "None"
        show_subscribe_button = True
        show_unsubscribe_button = False
        subscribe_return_url = self.request.uri
        unsubscribe_return_url = self.request.uri
        show_upload = False
        upload_url = blobstore.create_upload_url('/upload_photo')
        if user.user_id() == current_stream.owner:
        # The user owns the stream
            print "ViewStreamHandler: User owns the stream, no need to subscribe"
            show_subscribe_button = False
            no_subscribe_message = "You are the owner of the Stream"
            show_upload = True
        already_subscribed = False  # show Already Subscribed message instead of showing a button for subscribe
        for temp_user in current_stream.subscribers:  # this for loop is used to check the id of users
            if user.user_id() == temp_user.user_id():
                already_subscribed = True
                break
        if already_subscribed:
            show_subscribe_button = False
            show_unsubscribe_button = True
            no_subscribe_message = "You've already subscribed to the stream"

        template_values = {'String1': current_stream.name,
                           'url_list': PhotoUrls,
                           'fig_id_list': PhotoIdList,
                           'url_pages' : url_pages,
                           'num_of_pages': total_pages,
                           'nviews':current_stream.num_of_view,
                           'stream': current_stream,
                           'logout_url': users.create_logout_url('/'),
                           'no_subscribe_message': no_subscribe_message,
                           'show_subscribe_button': show_subscribe_button,
                           'show_unsubscribe_button': show_unsubscribe_button,
                           'show_upload': show_upload,
                           'upload_url':upload_url,
                           'subscribe_return_url': subscribe_return_url,
                           'unsubscribe_return_url': unsubscribe_return_url,}
        template = JINJA_ENVIRONMENT.get_template('refresh.html')
        self.response.write(template.render(template_values))

class GeoView(webapp2.RequestHandler):
    def get(self,id):

        user = users.get_current_user()
        if user is None:
        # go to login page
            print("View Stream Handler: Not logged in")
            self.redirect(users.create_login_page(self.request.uri))
            return

        # TODO: illegal stream id
        photo_info_list = []
        current_stream = stream.get_by_id(int(id))
        for photo in current_stream.figures:
            print('added photoinfo')
            print(str(photo.date))
            if(photo.external):
                photo_url = photo.ext_url
            else:
                photo_url = images.get_serving_url(photo.blob_key)

            current_info = {'time':(photo.date),
                            'lng':float(str(photo.location).split(',')[0]),
                            'lat':float(str(photo.location).split(',')[1]),
                            'url':photo_url}
            photo_info_list.append(current_info)
            print('added photoinfo')

        template_values = {'photo_info_list':photo_info_list,
                           'String1':current_stream.name
                           }
        template = JINJA_ENVIRONMENT.get_template('geoview.html')
        self.response.write(template.render(template_values))

class GeoViewFetch(webapp2.RequestHandler):
    #TODO: Deprecate
    def get(self,stream_id):
        self.response.headers['Content-Type'] = 'text/plain'
        current_stream = stream.get_by_id(int(stream_id))
        bkey = current_stream.figures[0].blob_key

        self.response.out.write(json.dumps({'upload_url':blobstore.create_upload_url('/upload_photo'), 'blob_key':str(bkey)}))


class DefaultViewStreamHandler(webapp2.RequestHandler):
    def get(self,id):
        self.redirect('/view/'+id+'/1')
        return

class DeleteStreamHandler(webapp2.RequestHandler):
    def get(self, id):
        user = users.get_current_user()
        if user is None:
        # go to login page
            print("View Stream Handler: Not logged in")
            self.redirect(users.create_login_page(self.request.uri))
            return

        #TODO: Illegal stream id


        current_stream = stream.get_by_id(int(id))
        if current_stream:
            #delete all the imgs, because they are huge
            for i in current_stream.figures:
                blobstore.delete(i.blob_key)
            queried_user_profile = user_profile.query(user_profile.user_id == user.user_id()).get()
            if queried_user_profile:
                if current_stream.name in queried_user_profile.own_streams:
                    queried_user_profile.own_streams.remove(str(current_stream.name))
                if (not queried_user_profile.own_streams) and (not queried_user_profile.subscibed_streams):
                    # no own_streams nor subscribed_streams
                    queried_user_profile.key.delete()
                else:
                    queried_user_profile.put()
            current_stream.key.delete()
        time_sleep(NDB_UPDATE_SLEEP_TIME)
        self.redirect('/management')
        return

class DeleteFigHandler(webapp2.RequestHandler):
    def get(self, id, fig_key):
        user = users.get_current_user()
        if user is None:
        # go to login page
            print("View Stream Handler: Not logged in")
            self.redirect(users.create_login_page(self.request.uri))
            return

        #TODO: illegal streamid or fig_key


        current_stream = stream.get_by_id(int(id))
        if current_stream:
            #delete all the imgs, because they are huge
            for i in current_stream.figures:
                if str(i.blob_key) == fig_key:
                    blobstore.delete(i.blob_key)
                    current_stream.figures.remove(i)
                    break

                dtstring = str(i.date)
                dtkey = re.sub("[^0-9]", "", dtstring)
                if dtkey == fig_key:
                    current_stream.figures.remove(i)


        current_stream.num_of_pics -= 1
        current_stream.put()
        time_sleep(NDB_UPDATE_SLEEP_TIME)
        self.redirect('/view/'+id+'/1')
        return

class MiniDeleteFigHandler(webapp2.RequestHandler):
    def get(self, id, fig_key):
        user = users.get_current_user()
        if user is None:
        # go to login page
            print("View Stream Handler: Not logged in")
            self.redirect(users.create_login_page(self.request.uri))
            return

        #TODO: illegal streamid or fig_key

        current_stream = stream.get_by_id(int(id))
        if current_stream:
            #delete all the imgs, because they are huge
            for i in current_stream.figures:
                if str(i.blob_key) == fig_key:
                    blobstore.delete(i.blob_key)
                    current_stream.figures.remove(i)
        current_stream.num_of_pics -= 1
        current_stream.put()
        time_sleep(NDB_UPDATE_SLEEP_TIME)

        return

class GenerateUploadUrlHandler(webapp2.RequestHandler):
      #
    def get(self, stream_id):
        self.response.headers['Content-Type'] = 'text/plain'
        current_stream = stream.get_by_id(int(stream_id))
        bkey = current_stream.figures[0].blob_key

        self.response.out.write(json.dumps({'upload_url':blobstore.create_upload_url('/upload_photo'), 'blob_key':str(bkey)}))


class UploadFromExtensionHandler(webapp2.RequestHandler):
      #
    def post(self):
      #  try:
            self.response.headers['Content-Type'] = 'text/plain'
            '''
            user = users.get_current_user()
            if user is None:
        # go to login page
                print("View Stream Handler: Not logged in")
                self.redirect(users.create_login_page(self.request.uri))
                return
            '''
            print('adding figure')
            stream_name = self.request.get("streamName")
            thiscomment = self.request.get("comment")
            image_url = self.request.get("imageUrl")
            geoLocation = self.request.get("geoLocation")
            geoString = geoLocation[1:-1].split(", ")
            Lat = geoString[0]
            Lng = geoString[1]
            print(image_url)
      # generate arbitrary key: since the blob_key is a combination of chars and numbers, using only numbers can avoid overlapping
            dt = datetime.now()
            print(dt)


            user_photo = image(owner = None,blob_key=None, comment = thiscomment, ext_url = str(image_url),
                           external = True, location=ndb.GeoPt(float(Lat),float(Lng)))
            user_photo.put()
        #seems redundant to fetch the stream
            stream_list = stream.query(stream.name == stream_name).fetch(1)
            current_stream = stream_list[0]
            returnmessage = "failed!"
            added = "false"
            if current_stream:
                returnmessage = "success"
                added = "true"
                current_stream.figures.insert(0, user_photo)
                current_stream.num_of_pics = len(current_stream.figures)

                current_stream.last_modified = str(dt.replace(microsecond = (dt.microsecond / 1000000) * 1000000))[:-3]
                current_stream.put()
            self.response.out.write(json.dumps({"msg": returnmessage, "added": added}))
      #  except:
       #     self.error(500)

class PhotoUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
       # self.redirect('/management')
        try:
            print ("PhotoUploadHandler: upload handler is running")
            upload = self.get_uploads()[0]
            print ("PhotoUploadHandler: upload resized")
            stream_name = self.request.get("stream_name")
            picloc=ndb.GeoPt(-57.32652122521709+114.65304245043419*random.random(),-123.046875+246.09375*random.random())
            user_photo = image(owner=users.get_current_user().user_id(),
                                   blob_key=upload.key(),comment = None,location = picloc)
            user_photo.put()
            queried_stream = stream.query(stream.name == stream_name).get()
            if queried_stream:
                queried_stream.figures.insert(0,user_photo)
                queried_stream.num_of_pics = len(queried_stream.figures)
                dt = datetime.now()
                queried_stream.last_modified = str(dt.replace(microsecond = (dt.microsecond / 1000000) * 1000000))[:-3]
                print "PhotoUploadHandler: put is being called"
                queried_stream.put()
            else:
                print ("PhotoUploadHander: No stream found matching "+stream_name)
            self.redirect('/view/%s' % queried_stream.key.id())
        except:
            self.error(500)






class CreateStreamHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()

        if user is None:
            print 'CreateStreamHandler: No user'
            self.redirect("/error/"+'You need to login')
            return
        stream_name = self.request.get('name').strip(" ")  #TODO: check whether name is not use
        if (not is_valid_stream_name(stream_name)):
        # empty stream_name should not be allowed
            print('CreateStreamHandler: Stream name not valid!')
            msg = "CreateStreamHandler: Stream name not valid!"
            self.redirect('/error/'+msg)
            return
        
        same_name_streams = stream.query(stream.name == stream_name).get()
        if (same_name_streams is not None):
            print 'CreateStreamHandler: Stream name existing, go to error page'
            msg = 'CreateStreamHandler: Stream name existing'
            self.redirect('/error/' + msg)
            return
        
        owner = user.user_id()
        
        parsed_tags = parse_tag(self.request.get('tag'))
        new_stream = stream(name=self.request.get('name'), owner = user.user_id(),
                            cover_url=self.request.get('cover_url'), tags=parsed_tags, figures=[], num_of_view = 0,
                            num_of_pics = 0)
        # new_stream = stream(name = 'test', owner = user.user_id(), cover_url = 'test_url',tags=[], figures = [])
        new_stream.put()
        # Create or update user profile
        queried_user_profile = user_profile.query(user_profile.user_id == user.user_id()).get()
        if not queried_user_profile:
            queried_user_profile = user_profile(user_id=user.user_id(), user_email=user.email(), own_streams=[], subscribed_streams=[])
        queried_user_profile.own_streams.append(new_stream.name)
        
        subscribers = parse_subscriber(self.request.get('subscriber'))
        for to_addr in subscribers:
            print to_addr
        subscribe_message = self.request.get('subscribe_message')
        invitation_email = mail.EmailMessage()
        invitation_email.sender = user.email()  # YW:sender is the creator of the stream
        invitation_email.subject = """Invitation to %(stream_name)s on Connexus from %(Invitor)s""" \
                          % {"stream_name": stream_name, "Invitor": user.nickname()}
        url_to_subscribe = (WEB_URL + '/subscribe/%s' % new_stream.key.id())
        # Print url to subscribe
        print ("CreateStreamHandler: URL to subscribe"+url_to_subscribe)
        template_values = {'stream_name': stream_name,
                           'subscribe_message': subscribe_message,
                           'subscribe_stream_url': url_to_subscribe,
                           'logout_url': users.create_logout_url('/')}
        template = JINJA_ENVIRONMENT.get_template('subscribe_invitation_email.html')
        
        invitation_email.body = (INVITATION_EMAIL_PLAIN_TEXT % {'user': new_stream.owner,
                                                                'stream_name': new_stream.name,
                                                                'message': subscribe_message,
                                                                'subscribe_stream_url': url_to_subscribe})
        invitation_email.html = template.render(template_values)
        #logging.debug(invitation_email.body)
        receiver_addrs = []
        for to_addr in subscribers:
            if mail.is_email_valid(to_addr):
                receiver_addrs.append(to_addr)
        if receiver_addrs:
            invitation_email.to = receiver_addrs
            invitation_email.send()

        time_sleep(NDB_UPDATE_SLEEP_TIME)
        #self.redirect(('/view/%s' % str(new_stream.key.id())))
        self.redirect('/management')

class TrendReportHandler(webapp2.RequestHandler):
    def get(self, freq):
        if int(freq) == 1:
            subscriber_list = trend_subscribers.query(trend_subscribers.report_freq == '5 mins').fetch()
        elif int(freq) == 2:
            subscriber_list = trend_subscribers.query(trend_subscribers.report_freq == '1 hour').fetch()
        elif int(freq) == 4:
            subscriber_list = trend_subscribers.query(trend_subscribers.report_freq == 'everyday').fetch()
        else: subscriber_list = []
        print "TrendReportHandler: trend sending"

        stream_list = stream.query().order(-stream.num_of_view).fetch(3)

        to_list = []
        for s in subscriber_list:
            to_list.append(s.user_email)

        if (len(stream_list) == 3):

                cmail = mail.EmailMessage(sender = "Connexus Support <support@just-plate-107116.appspotmail.com>", subject = "Connexus Digest")
                cmail.to = to_list
                cmail.body = """ Hello, following is your connexus digest. The top 3 most popular stream are:
                %(name1)s, %(name2)s, %(name3)s. To check the detail please click thru the following link:
                %(trending_url)s
                """ % {'name1':stream_list[0].name,
                       'name2':stream_list[1].name,
                       'name3':stream_list[2].name,
                       'trending_url':'http://just-plate-107116.appspot.com/stream_trending'}
                cmail.send()

        elif (len(stream_list) == 2):

                cmail = mail.EmailMessage(sender = "Connexus Support <support@just-plate-107116.appspotmail.com>", subject = "Connexus Digest")
                cmail.to = to_list
                cmail.body = """ Hello, following is your connexus digest. The top 2 most popular stream are:
                %(name1)s, %(name2)s. To check the detail please click thru the following link:
                %(trending_url)s
                """ % {'name1':stream_list[0].name,
                       'name2':stream_list[1].name,
                       'trending_url':'http://just-plate-107116.appspot.com/stream_trending'}
                cmail.send()

        elif (len(stream_list) == 1):

                cmail = mail.EmailMessage(sender = "Connexus Support <support@just-plate-107116.appspotmail.com>", subject = "Connexus Digest")
                cmail.to = to_list
                cmail.body = """ Hello, following is your connexus digest. The top 1 most popular stream are:
                %(name1)s. To check the detail please click thru the following link:
                %(trending_url)s
                """ % {'name1':stream_list[0].name,
                       'trending_url':'http://just-plate-107116.appspot.com/stream_trending'}
                cmail.send()
        else:

                cmail = mail.EmailMessage(sender = "Connexus Support <support@just-plate-107116.appspotmail.com>", subject = "Connexus Digest")
                cmail.to = to_list
                cmail.body = """ Hello, following is your connexus digest. Sorry at this time we do not have any stream.
                 To check the detail please click thru the following link:
                %(trending_url)s
                """ % {'trending_url':'http://just-plate-107116.appspot.com/stream_trending'}
                cmail.send()


class TrendingFrequencyHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        trend_slist = trend_subscribers.query(trend_subscribers.user_email == 'adnan.aziz@gmail.com').fetch()
        if len(trend_slist)==0:
            trend_subscribers(user_email = 'adnan.aziz@gmail.com', report_freq = '0').put()
        trend_slist = trend_subscribers.query(trend_subscribers.user_email == 'nima.dini@utexas.edu').fetch()
        if len(trend_slist)==0:
            trend_subscribers(user_email = 'nima.dini@utexas.edu', report_freq = '0').put()
        trend_slist = trend_subscribers.query(trend_subscribers.user_email == 'kevzsolo@gmail.com').fetch()
        if len(trend_slist)==0:
            trend_subscribers(user_email = 'kevzsolo@gmail.com', report_freq = '0').put()
        trend_slist = trend_subscribers.query(trend_subscribers.user_email == 'jxzheng39@gmail.com').fetch()
        if len(trend_slist)==0:
            trend_subscribers(user_email = 'jxzheng39@gmail.com', report_freq = '0').put()

        if user is None:
            self.redirect("/error/"+'You need to login')
            return

        subscriber_list = trend_subscribers.query()
        print(str(subscriber_list))
        flag = False

        to_list = []
        for s in subscriber_list:
            #this is the version for testing
            s.report_freq = (self.request.get("frequency"))
            s.put()
            to_list.append(s.user_email)

        cmail = mail.EmailMessage(sender = user.email(), subject = "Connexus Digest: trending frequency changed")
        cmail.to = to_list
        cmail.body = "Your trend updating frequency has been changed"
        cmail.send()

        ''' this is the version for real world
            if s.user_email == str(user.email()):
                try:
                    s.report_freq = (self.request.get("frequency"))
                    s.put()
                except:
                    s.report_freq = '0'
                    s.put()
                flag = True
                break
        if(not flag):
            try:
                new_subscriber = trend_subscribers(user_email = user.email(), report_freq = (self.request.get("frequency")))
            except:
                new_subscriber = trend_subscribers(user_email = user.email(), report_freq = '0')
            new_subscriber.put()
            '''
        self.redirect("/stream_trending")
        ''' #this is the version for real world
        cmail = mail.EmailMessage(sender = "Connexus Support <support@just-plate-107116.appspotmail.com>", subject = "Connexus Digest: trending frequency changed")
        cmail.to = user.email()
        cmail.body = "You have changed your updating preference."
        cmail.send()
        '''



class SubscribeStreamHandler(webapp2.RequestHandler):
    """Handle subscription to one stream"""

    def get(self, stream_id):
        """Display stream name, display cover, provide two buttons: 1)Subscribe 2)Return to return_url"""
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
            return
        return_url = str(self.request.get('return_url', DEFAULT_RETURN_URL))
        print ("SubscribeStreamHandler: Return URL: " + return_url)
        # YW: default return url is /management, or return to the url specified
        queried_stream = stream.get_by_id(int(stream_id))
        if queried_stream is None: # stream not found
            self.redirect('/error/'+'Stream not found')
            return
            
        # YW: check whether there should be a button for subscribe
        no_subscribe_message = "None"
        show_subscribe_button = True
        if user.user_id() == queried_stream.owner:
        # The user owns the stream
            print ("SubscribeStreamHandler: "+"User owns the stream, no need to subscribe")
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
                           'logout_url': users.create_logout_url('/'),
                           'return_url': return_url,
                           'show_subscribe_button': show_subscribe_button,
                           'no_subscribe_message': no_subscribe_message}
        self.response.write(template.render(template_values))


class ConfirmSubscribeStreamHandler(webapp2.RequestHandler):
    """Confirm subscription to stream, only contains post method"""
    def post(self):
        """Subscribe to the stream: 1.add stream to user's stream set; 2.add user to stream's subscriber list;
        3. redirect to manage page"""
        #print("Enter post method")
        user = users.get_current_user()
        return_url = str(self.request.get('return_url','/'))
        stream_id = int(self.request.get('stream_id'))
        print ('ConfirmSubscribeStreamHandler: Return Url: '+return_url)
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
        queried_user_profile = user_profile.query(user_profile.user_id == user.user_id()).get()
        if not queried_user_profile:
            queried_user_profile = user_profile(user_id=user.user_id(), user_email=user.email(), own_streams=[], subscribed_streams=[])
        queried_user_profile.subscribed_streams.append(queried_stream.name)
        queried_user_profile.put()

        self.redirect(return_url)


# Helper functions
# [Helper function for CreateStreamHandler]
def parse_subscriber(subscriber_string):
    """This function parse the email addresses from string"""
    if subscriber_string == '':
        return []
    else:
        splitter = r'[,;\t\r\n\s]'
        subscribers = re.split(splitter, subscriber_string)
        return subscribers
        
def parse_tag(tag_string):
    """Parse tags from string"""
    # tags = filter(None, re.sub('[ ,;\t\n\r]','',tag_string).split('#'))
    tags = re.findall(r'#[A-Za-z0-9]+',tag_string)
    return tags
    
def is_valid_stream_name(name_string):
    """Check whether the stream name is valid"""
    name_string = name_string.strip(" ")
    if (not name_string):
        return False
    if re.match(r"[~\!@#\$%\^&\*\(\)\+{}:;\[\]\r\n\t]", name_string):
        return False
    name_words = filter(None, re.split(r'[\s]', name_string))
    if not name_words:
        return False
    plain_word_regex = re.compile(r"^[A-Za-z0-9]+[A-Za-z0-9\'-_]+$")
    for name_word in name_words:
        if not plain_word_regex.match(name_word):
            return False
    return True

def parse_search_keyword(key_word_string):    
    """Parse key words for search stream"""
    keywords = {'plain_keywords':[],
                'tags':[]}  # YW: Can extend to contain @user search later
    keywords['tags'] = re.findall('#[A-Za-z0-9]+', key_word_string)
    print ('parse_search_keyword: tags: ' + " ".join(keywords['tags']))
    # print key_word_string
    original_words = filter(None, re.split(r'[,;\t\n\r\s]', key_word_string))
    # print original_words
    plain_keyword_reg = re.compile(r"[A-Za-z0-9\'\-_]+")  # YW: allow prime and hyphen
    plain_keyword_reg_start = re.compile(r"^[A-Za-z0-9]+")
    # tags_reg = re.compile('^#[a-zA-Z0-9]+$')
    for word in original_words:
        # print word
        if plain_keyword_reg.match(word) and plain_keyword_reg_start.match(word):
            keywords['plain_keywords'].append(word)
    print ('parse_search_keyword: plain keywords: ' + " ".join(keywords['plain_keywords']))
    return keywords
    
        
class SearchHandler(webapp2.RequestHandler):
    def get(self):
        MAX_RESULT_NUM = 5
        original_keyword_string = self.request.get('search_keywords')
        print ('SearchHandler: original string: '+original_keyword_string)
        keywords = parse_search_keyword(original_keyword_string)
      # general searching:
        queried_keywords = (keywords['plain_keywords'] + keywords['tags'])
        queried_streams = []
        if queried_keywords:
            # allow to check matching part of the string
            all_streams = stream.query().order(-stream.num_of_view, -stream.num_of_pics)
            for temp_stream in all_streams:
                temp_stream_words = []
                temp_stream_words.extend(filter(None, re.split(r'[\s]',temp_stream.name)))
                temp_stream_words.extend(temp_stream.tags)
                temp_stream_string = " ".join(list(set(temp_stream_words) - constants.CACHED_STOP_WORDS)).lower()
                if any(temp_keyword.lower() in temp_stream_string for temp_keyword in queried_keywords):
                    queried_streams.append(temp_stream) 
                if len(queried_streams) == MAX_RESULT_NUM:
                    break
        print ('SearchHandler: set of key words: ' + "/".join(queried_keywords))
        template_values = {'original_keyword_string': original_keyword_string,
                           'queried_keywords': queried_keywords,
                           'queried_streams': queried_streams,
                           'logout_url': users.create_logout_url('/')}
        template = JINJA_ENVIRONMENT.get_template('search_temp.html')
        self.response.write(template.render(template_values))
        
class UnsubscribeStreamHandler(webapp2.RequestHandler):
    def post(self):
        user = users.get_current_user()
        if user is None:
            self.redirect(users.create_login_url(self.request.uri))
            return        
        return_url = str(self.request.get('return_url','/'))
        stream_id = int(self.request.get('stream_id'))
        print ('UnsubscribeHandler: Return Url: '+ return_url)
        queried_stream = stream.get_by_id(stream_id)
        if queried_stream:
            for temp_user in queried_stream.subscribers:
                if user.user_id() == temp_user.user_id():
                    queried_stream.subscribers.remove(temp_user)
                    queried_stream.put()
                    break
            queried_user_profile = user_profile.query(user_profile.user_id == user.user_id()).get()
            if queried_user_profile:
                queried_user_profile.subscribed_streams.remove(queried_stream.name)
                if  (not queried_user_profile.own_streams) and (not queried_user_profile.subscribed_streams):
                    # no own_streams nor subscribed_streams
                    queried_user_profile.key.delete()
                else:
                    queried_user_profile.put()
        
        time_sleep(NDB_UPDATE_SLEEP_TIME)
        self.redirect(return_url)
        
