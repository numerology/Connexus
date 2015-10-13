__author__ = 'Yicong'
import webapp2
from google.appengine.ext import ndb
from api_handler import *
from handlers import *
import constants
from constants import CompletionIndex
import re
import json


def parsegeolocation(geostring):
    geolocation = {"lat": 0.0, "lng": 0.0}
    if not geostring:
        return geolocation
    else:
        temp_string = re.sub(r'[()]','', geostring)
        location = filter(None, re.split(r'[ ,\s\r\t\n]', temp_string))
        if len(location) == 2:
            geolocation["lat"] = float(location[0])
            geolocation["lng"] = float(location[1])
        return geolocation


class ExtensionUploadHandler(webapp2.RequestHandler):
    def post(self):
        stream_name = str(self.request.get("streamName"))
        comment = str(self.request.get("comment"))
        image_url = str(self.request.get("imageUrl"))
        geolocation = parsegeolocation(str(self.request.get("geoLocation")))
        print ("Extension Upload: stream name: " + stream_name)
        print ("comment: " + comment)
        # print ("imageUrl: " + imageurl)
        print ("geoLocation: " + str(self.request.get("geoLocation")))
        print ("lat: " + str(geolocation["lat"]) + " lng: " + str(geolocation["lng"]))
        Lat = geolocation["lat"]
        Lng = geolocation["lng"]
        dt = datetime.now()
        print(dt)
        added = "false"
        queried_stream = stream.query(stream.name == stream_name).get()
        if queried_stream:
            returnmessage = "Stream found, image added"
            added = "true"
            user_photo = image(owner = None,blob_key=None, comment = comment, ext_url = str(image_url),
                       external = True, location=ndb.GeoPt(float(Lat), float(Lng)))
            user_photo.put()
            queried_stream.figures.insert(0, user_photo)
            queried_stream.num_of_pics = len(queried_stream.figures)
            queried_stream.last_modified = str(dt.replace(microsecond = (dt.microsecond / 1000000) * 1000000))[:-3]
            queried_stream.put()
        else:
            returnmessage = "Stream name not found!"
        data = {"message": returnmessage, "added": added}
        self.response.write(json.dumps(data, sort_keys=True))
