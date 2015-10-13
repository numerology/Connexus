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
        streamname = str(self.request.get("streamName"))
        comment = str(self.request.get("comment"))
        imageurl = str(self.request.get("imageUrl"))
        geolocation = parsegeolocation(str(self.request.get("geoLocation")))
        print ("Extension Upload: stream name: " + streamname)
        print ("comment: " + comment)
        # print ("imageUrl: " + imageurl)
        print ("geoLocation: " + str(self.request.get("geoLocation")))
        print ("lat: " + str(geolocation["lat"]) + " lng: " + str(geolocation["lng"]))
        returnmessage = ""
        queried_stream = stream.query(stream.name == streamname).get()
        if queried_stream:
            returnmessage = "Stream found, image added"
        else:
            returnmessage = "Stream name not found!"
        data = {"message": returnmessage}
        self.response.write(json.dumps(data, sort_keys=True))
