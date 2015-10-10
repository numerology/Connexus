__author__ = 'Yicong'
#import cgi
import webapp2
#import os
import re
#import jinja2
import json
import ndb
import constants

WORD_LIST = ["Babel", "Car", "Dag", "Texas", "Van", "Zebra", "Adnan", "Algorithm", "Austin", ]


class AutoCompleteHandler(webapp2.RequestHandler):
    # return auto complete suggestions based on keywords
    def get(self):
        keywords = filter(None, re.split(r'[,;\t\n\r\s]', str(self.request.get("keywords")).lower()))
        result = []
        for word in constants.AUTO_COMPLETION_INDEX[:]:  # copy
            if any(key in word.lower() for key in keywords):
                result.append(word)
                if len(result) == constants.AUTO_COMPLETE_LENGTH:
                    break
        if result:
            result.sort()
        print ("AutoCompleteHandler: keywords is " + " ".join(keywords))
        self.response.write(json.dumps(result, sort_keys=True))
