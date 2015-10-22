__author__ = 'Jiaxiao Zheng'

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
import constants
import random
import json
from api_handler import *
from ExtensionUploadHandler import *

class GetUploadUrlHandler(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'

        self.response.out.write(json.dumps({'upload_url':str(blobstore.create_upload_url('/mobile/upload_photo'))}))

class MobilePhotoUploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
       # self.redirect('/management')
        try:
            print ("PhotoUploadHandler: upload handler is running")
            upload = self.get_uploads()[0]
            print ("PhotoUploadHandler: upload resized")
            stream_name = self.request.get("stream_name")
            locationstring = self.request.get("geo_location")
            location = parsegeolocation(locationstring)

            picloc=ndb.GeoPt(location["lat"],location["lng"])
            user_photo = image(owner=None,
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
        except:
            self.error(500)
