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
from math import radians, cos, sin, asin, sqrt
from ExtensionUploadHandler import *

def haversine(lon1, lat1, lon2, lat2):

    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    return km

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

            picloc=ndb.GeoPt(location["lat"]+0.005*(random.random()-0.5),location["lng"]+0.005*(random.random()-0.5))
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

class MobileListHandler(webapp2.RequestHandler):
    def get(self):
        cover_url = []
        streams_id = []
        try:
            stream_list = stream.query().order(stream.creation_time).fetch()
            for s in stream_list:
                cover_url.append(str(s.cover_url))
                streams_id.append(str(s.key.id()))

            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(json.dumps({'cover_url':cover_url, 'streams_id':streams_id}))

        except:
            self.error(500)

class MobileViewStreamHandler(webapp2.RequestHandler):
    def get(self):
        try:
            stream_id = self.request.get("stream_id")
            current_stream = stream.get_by_id(int(stream_id))
            PhotoUrls = []
            for img in current_stream.figures:
                if(not img.external):
                    PhotoUrls.append(images.get_serving_url(img.blob_key))
                else:
                    PhotoUrls.append(str(img.ext_url))
            stream_name = current_stream.name
            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(json.dumps({'image_url':PhotoUrls, 'stream_name':stream_name}))
        except:
            self.error(500)

class MobileViewNearbyHandler(webapp2.RequestHandler):
    def get(self):
        try:
            locationstring = self.request.get("geolocation")
            location = parsegeolocation(locationstring)
            #Search through all streams
            img_list = []
            stream_list = stream.query()
            for s in stream_list:
                for img in s.figures:
                    if(haversine(location["lng"],location["lat"],img.location["lng"],img.location["lat"]) < 10):
                        img_list.append({'img':img,
                                         'dist':haversine(location["lng"],location["lat"],img.location["lng"],img.location["lat"]),
                                         'stream_id':str(s.key.id())})

            img_list = sorted(img_list, key = lambda img: img['dist'])

            PhotoUrls = []
            StreamIDs = []
            for img in img_list:
                StreamIDs.append(img['stream_id'])
                if(not img.external):
                    PhotoUrls.append(images.get_serving_url(img['img'].blob_key))
                else:
                    PhotoUrls.append(str(img['img'].ext_url))


            self.response.headers['Content-Type'] = 'text/plain'
            self.response.out.write(json.dumps({'image_url':PhotoUrls, 'stream_ids':StreamIDs}))
        except:
            self.error(500)