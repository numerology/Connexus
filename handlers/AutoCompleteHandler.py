__author__ = 'Yicong'
#import cgi
import webapp2
#import os
import re
#import jinja2
import json
from google.appengine.ext import ndb
import constants
from constants import CompletionIndex

WORD_LIST = ["Babel", "Car", "Dag", "Texas", "Van", "Zebra", "Adnan", "Algorithm", "Austin", ]


class AutoCompleteHandler(webapp2.RequestHandler):
    # return auto complete suggestions based on keywords
    def get(self):
        print str(self.request.get("keywords"))
        no_backslash_string = str(self.request.get("keywords")).replace("\\"," ")
        keywords = filter(None, re.split(r'[ ,;\t\n\r\s]', no_backslash_string.lower() ) )
        result = []
        completion_words = []
        completion_index = CompletionIndex.query().get()
        if completion_index:
            completion_words = completion_index.keywords
        print completion_words
        for word in completion_words:  # copy
            if any(key in word.lower() for key in keywords):
                result.append(word)
                if len(result) == constants.AUTO_COMPLETE_LENGTH:
                    break
        if result:
            result.sort()
        print ("AutoCompleteHandler: keywords is " + " ".join(keywords))
        self.response.write(json.dumps(result, sort_keys=True))