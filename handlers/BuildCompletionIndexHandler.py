__author__ = 'Yicong'
import webapp2
from google.appengine.ext import ndb
from api_handler import *
from handlers import *
import constants
from constants import CompletionIndex
import re


class BuildCompletionIndexHandler(webapp2.RequestHandler):
    def get(self):
        print "Run BuildCompletionIndexHandler"
        keywords = []
        known_keywords = set()
        completionindex = CompletionIndex.query().get()
        if not completionindex:
            # No completionindex existing
            completionindex=CompletionIndex(keywords=[])
        streams = stream.query().order(-stream.num_of_view, -stream.num_of_pics)
        for temp_stream in streams:
            for temp_word in extract_stream_keywords(temp_stream):
                if temp_word in known_keywords:
                    continue
                keywords.append(temp_word)
                known_keywords.add(temp_word)

        completionindex.keywords = keywords
        completionindex.put()


def extract_stream_keywords(temp_stream):
    raw_keywords = []
    if temp_stream:
        raw_keywords.extend(filter(None, re.split(r'[ ,;\t\r\n\s]', str(temp_stream.name))))
        raw_keywords.extend(temp_stream.tags)
        for temp_image in temp_stream.figures:
            if temp_image.comment:
                raw_keywords.extend(filter(None, re.split(r'[ ,;\t\r\n\s]', str(temp_image.comment))))
    # print set(raw_keywords)
    # print constants.CACHED_STOP_WORDS
    keywords = list(set(raw_keywords)-constants.CACHED_STOP_WORDS)
    return keywords
